"""Kiểm thử thực tế: mã hóa/giải mã video và âm thanh, không dùng dịch vụ mạng."""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import threading
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

import av
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from scene_data import validate_annotation
from render_stream_whiteboard import RegionStreamRenderer
from stream_render import Config, _transcode_with_pyav
from video_io import CancelledError, run_ffmpeg
from studio.project import (new_project, new_scene, save_project, load_project,
                            prepared_scene, import_asset, audio_duration_ms)
from studio.render import render_project


def inspect_video(path):
    with av.open(str(path)) as video:
        stream = video.streams.video[0]
        info = (stream.width, stream.height, stream.average_rate, stream.codec_context.name)
        frames = list(video.decode(video=0))
    with av.open(str(path)) as audio:
        streams = list(audio.streams.audio)
        samples = [frame.to_ndarray() for frame in audio.decode(audio=0)] if streams else []
    return info, frames, samples


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='thu-nghiem-')
        self.root = Path(self.temp.name) / "Dự án có dấu và 'nháy'"
        self.root.mkdir()
        self.image = self.root / 'ảnh minh họa.png'
        image = Image.new('RGB', (320, 180), '#F6F1E3')
        draw = ImageDraw.Draw(image)
        draw.ellipse((30, 20, 140, 160), outline='#202020', width=5)
        draw.rectangle((190, 50, 290, 130), outline='#202020', width=5)
        image.save(self.image)
        self.voice = self.root / 'giọng đọc.wav'
        with wave.open(str(self.voice), 'wb') as out:
            out.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
            tone = (np.sin(np.arange(16000)*2*np.pi*440/16000)*9000).astype('<i2')
            out.writeframes(tone.tobytes())

    def tearDown(self):
        self.temp.cleanup()

    def project(self, aspect='16:9', audio=True):
        project = new_project('Thử nghiệm tiếng Việt')
        project['aspectRatio'] = aspect
        scene = new_scene('Xin chào Việt Nam!')
        scene.update(image=self.image.name, durationMs=1200, audio=self.voice.name if audio else '')
        project['scenes'] = [scene]
        return project

    def test_project_portable_roundtrip_and_invalid_duration(self):
        p = self.project()
        p['scenes'][0]['image'] = import_asset(self.image, self.root)
        target = self.root / 'du-an.json'
        save_project(p, target)
        self.assertEqual(load_project(target), p)
        p['scenes'][0]['durationMs'] = float('nan')
        with self.assertRaises(ValueError):
            save_project(p, target)
        self.assertEqual(load_project(target)['name'], 'Thử nghiệm tiếng Việt')

    def test_audio_duration_and_reject_truncation(self):
        self.assertLess(abs(audio_duration_ms(self.voice)-1000), 34)
        from studio.project import validate_project
        p = self.project()
        p['scenes'][0]['durationMs'] = 100
        with self.assertRaises(ValueError):
            validate_project(p, self.root)

    def annotation(self):
        return {'canvas': {'width': 320, 'height': 180}, 'sceneDurationMs': 1500, 'elements': [
            {'sequence': 1, 'region': {'x': 0, 'y': 0, 'width': 180, 'height': 180}, 'reveal': {'startMs': 100, 'durationMs': 400}},
            {'sequence': 2, 'region': {'x': 160, 'y': 0, 'width': 160, 'height': 180}, 'reveal': {'startMs': 600, 'durationMs': 400}}]}

    def test_annotation_overlap_bounds_and_mask(self):
        ann = self.annotation()
        validated = validate_annotation(ann, (320, 180))
        renderer = RegionStreamRenderer(np.array(Image.open(self.image))[:, :, ::-1].copy(), validated,
                                        Config(fps=30, output_width=320, output_height=180), None, True)
        mask = renderer._allowed_mask(ann['elements'][0], ann['elements'][1:])
        self.assertFalse(mask[:, 160:].any())
        ann['elements'][1]['reveal']['startMs'] = 200
        with self.assertRaises(ValueError):
            validate_annotation(ann)
        ann = self.annotation()
        ann['elements'][1]['region']['width'] = 1000
        with self.assertRaises(ValueError):
            validate_annotation(ann)

    def test_blank_and_fully_masked_regions_exact_frames(self):
        for mode in ['grid', 'skeleton']:
            with self.subTest(mode=mode):
                ann = self.annotation()
                ann['elements'][1]['region'] = copy.deepcopy(ann['elements'][0]['region'])
                blank = np.full((180, 320, 3), 245, dtype=np.uint8)
                renderer = RegionStreamRenderer(blank, ann, Config(fps=30, output_width=320, output_height=180, ink_path_mode=mode), None, True)
                target = self.root / f'blank-{mode}.mp4'
                renderer.render_to(target, 1500)
                info, frames, _ = inspect_video(target)
                self.assertEqual(len(frames), 45)
                self.assertEqual(info[:2], (320, 180))

    def test_legacy_pyav_transcode_packet_iteration(self):
        source = self.root / 'raw.mp4'
        target = self.root / 'h264.mp4'
        p = self.project(audio=False)
        render_project(p, self.root, source, preview=True)
        _transcode_with_pyav(source, target)
        self.assertEqual(inspect_video(target)[0][3], 'h264')

    def test_real_full_hd_both_ratios_with_hand_and_audio(self):
        for aspect, size in [('16:9', (1920, 1080)), ('9:16', (1080, 1920))]:
            with self.subTest(aspect=aspect):
                p = self.project(aspect)
                target = self.root / ('ngang.mp4' if aspect == '16:9' else 'dọc.mp4')
                render_project(p, self.root, target)
                info, frames, audio = inspect_video(target)
                self.assertEqual(info[:2], size)
                self.assertEqual(info[2], 30)
                self.assertEqual(info[3], 'h264')
                self.assertEqual(len(frames), 36)
                self.assertTrue(audio)
                self.assertGreater(max(np.abs(a).max() for a in audio), 0.05)
                self.assertIn('Xin chào Việt Nam!', target.with_suffix('.srt').read_text(encoding='utf-8-sig'))
                first = frames[0].to_ndarray(format='rgb24').astype(float)
                self.assertLess(first.std(axis=(0, 1)).max(), 4)
                self.assertGreater(frames[-1].to_ndarray(format='gray').std(), 5)
                if os.environ.get('WHITEBOARD_TEST_OUTPUT'):
                    import shutil
                    artifact = Path(os.environ['WHITEBOARD_TEST_OUTPUT'])
                    artifact.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, artifact / target.name)
                    shutil.copy2(target.with_suffix('.srt'), artifact / target.with_suffix('.srt').name)
                    Image.fromarray(frames[len(frames)//3].to_ndarray(format='rgb24')).save(artifact / (target.stem+'-ban-tay.png'))

    def test_preview_multi_scene_audio_and_legacy_merge(self):
        p = self.project()
        second = copy.deepcopy(p['scenes'][0])
        second.update(id='scene-2', audio='', script='Cảnh thứ hai.')
        p['scenes'].append(second)
        target = self.root / 'xem trước.mp4'
        render_project(p, self.root, target, preview=True)
        info, frames, audio = inspect_video(target)
        self.assertEqual(info[:2], (640, 360))
        self.assertEqual(len(frames), 72)
        self.assertTrue(audio)
        self.assertIn('00:00:01,200 --> 00:00:02,400', target.with_suffix('.srt').read_text(encoding='utf-8-sig'))
        from merge_scenes import _ffmpeg_concat_copy
        merged = self.root / 'ghép.mp4'
        self.assertTrue(_ffmpeg_concat_copy([target, target], merged))
        self.assertEqual(len(inspect_video(merged)[1]), 144)

    def test_letterbox_and_legacy_annotation(self):
        p = self.project('9:16')
        annotation = self.root / 'vùng.json'
        annotation.write_text(json.dumps(self.annotation()), encoding='utf-8')
        p['scenes'][0]['annotation'] = annotation.name
        image, ann = prepared_scene(p['scenes'][0], self.root, (360, 640))
        self.assertEqual(image.size, (360, 640))
        self.assertEqual(image.getpixel((0, 0)), (246, 241, 227))
        self.assertEqual(ann['canvas'], {'width': 360, 'height': 640})
        validate_annotation(ann, image.size)

    def test_cancel_preserves_previous_export(self):
        target = self.root / 'giữ nguyên.mp4'
        target.write_bytes(b'previous-export')
        cancel = threading.Event()
        cancel.set()
        with self.assertRaises(CancelledError):
            render_project(self.project(), self.root, target, preview=True, cancel=cancel)
        self.assertEqual(target.read_bytes(), b'previous-export')
        self.assertFalse(list(self.root.glob('whiteboard-*')))

    def test_missing_files_and_input_overwrite(self):
        p = self.project()
        p['scenes'][0]['image'] = 'khong-co.png'
        with self.assertRaises(ValueError):
            render_project(p, self.root, self.root / 'out.mp4')
        p = self.project()
        p['scenes'][0]['image'] = 'bad.png'
        (self.root / 'bad.png').write_text('invalid image')
        with self.assertRaises(Exception):
            render_project(p, self.root, self.root / 'out.mp4')

    def test_cancel_during_render_cleans_temporary_files(self):
        target = self.root / 'huy-giua-chung.mp4'
        target.write_bytes(b'previous-export')
        cancel = threading.Event()
        def progress(amount, message):
            cancel.set()
        with self.assertRaises(CancelledError):
            render_project(self.project(), self.root, target, preview=True, progress=progress, cancel=cancel)
        self.assertEqual(target.read_bytes(), b'previous-export')
        self.assertFalse(list(self.root.glob('whiteboard-*')))


if __name__ == '__main__':
    unittest.main()
