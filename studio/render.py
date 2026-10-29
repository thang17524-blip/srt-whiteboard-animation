from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from render_stream_whiteboard import RegionStreamRenderer
from stream_render import Config
from video_io import CancelledError, run_ffmpeg
from .project import SIZES, PAPER, prepared_scene, resolve_asset, validate_project


def srt_time(milliseconds):
    ms = round(milliseconds)
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds, ms = divmod(ms, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{ms:03}'


def render_project(project, root, output, preview=False, progress=None, cancel=None):
    validate_project(project, root)
    output = Path(output).resolve()
    if output.suffix.lower() != '.mp4':
        raise ValueError('Tên tệp xuất phải có phần mở rộng .mp4.')
    inputs = {resolve_asset(root, s.get(key)) for s in project['scenes'] for key in ('image', 'audio', 'annotation') if s.get(key)}
    if output in inputs:
        raise ValueError('Không thể ghi đè lên tệp đầu vào.')
    output.parent.mkdir(parents=True, exist_ok=True)
    size = SIZES[project['aspectRatio']]
    if preview:
        size = (640, 360) if project['aspectRatio'] == '16:9' else (360, 640)
    cfg = Config(fps=30, output_width=size[0], output_height=size[1],
                 canvas_hex=PAPER, target_hand_height=round(min(size)*0.45))
    count = len(project['scenes'])
    subtitles, offset = [], 0
    # Chỉ thay tệp đích sau khi hoàn tất; hủy/lỗi không phá bản xuất trước.
    with tempfile.TemporaryDirectory(prefix='whiteboard-', dir=output.parent) as folder:
        work = Path(folder)
        rendered = []
        for i, scene in enumerate(project['scenes']):
            if cancel is not None and cancel.is_set():
                raise CancelledError('Đã hủy tạo video.')
            image, ann = prepared_scene(scene, root, size)
            raw = work / f'raw-{i}.mp4'
            # PCM trong MOV không có độ trễ AAC ở mỗi cảnh. Chỉ mã hóa AAC một lần
            # sau khi nối để không cộng dồn khoảng trễ bộ mã hóa qua nhiều cảnh.
            clip = work / f'clip-{i}.mov'
            renderer = RegionStreamRenderer(np.asarray(image)[:, :, ::-1].copy(), ann, cfg,
                                            ROOT / 'assets/drawing-hand.png', not project.get('showHand', True))
            def report(value):
                if progress:
                    progress((i + value * 0.85) / count, f'Đang vẽ cảnh {i+1}/{count}')
            renderer.render_to(raw, ann['sceneDurationMs'], report, cancel)
            duration = ann['sceneDurationMs'] / 1000
            audio = resolve_asset(root, scene.get('audio'))
            if audio:
                audio_args = ['-i', audio]
            else:
                audio_args = ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo']
            run_ffmpeg(['-i', raw, *audio_args, '-map', '0:v:0', '-map', '1:a:0',
                        '-c:v', 'copy', '-af', 'apad', '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2',
                        '-t', f'{duration:.6f}', '-movflags', '+faststart', clip], cancel)
            rendered.append(clip)
            if scene.get('script', '').strip():
                subtitles.append(f'{len(subtitles)+1}\n{srt_time(offset)} --> {srt_time(offset+ann["sceneDurationMs"])}\n{scene["script"].strip()}\n')
            offset += ann['sceneDurationMs']
            if progress:
                progress((i+1)/count*0.98, f'Đã dựng cảnh {i+1}/{count}')
        listing = work / 'clips.txt'
        listing.write_text(''.join("file '" + str(p.resolve()).replace('\\', '/').replace("'", "'\\''") + "'\n" for p in rendered), encoding='utf-8')
        combined = work / 'complete.mp4'
        run_ffmpeg(['-f', 'concat', '-safe', '0', '-i', listing, '-c:v', 'copy',
                    '-c:a', 'aac', '-ar', '48000', '-ac', '2', '-t', f'{offset/1000:.6f}',
                    '-movflags', '+faststart', combined], cancel)
        if cancel is not None and cancel.is_set():
            raise CancelledError('Đã hủy tạo video.')
        subtitle_file = work / 'complete.srt'
        subtitle_file.write_text('\n'.join(subtitles), encoding='utf-8-sig')
        os.replace(subtitle_file, output.with_suffix('.srt'))
        os.replace(combined, output)
    if progress:
        progress(1, 'Đã hoàn tất video')
    return output
