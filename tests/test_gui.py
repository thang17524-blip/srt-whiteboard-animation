"""Thực thi widget Tk thật; chỉ thay hộp chọn tệp và trình phát ngoài bằng mock."""
import copy
import sys
import tempfile
import time
import wave
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studio.gui import StudioApp
from studio.project import load_project


class GuiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = StudioApp(self.root)
        self.root.update()
        self.errors = []
        self.error_patch = patch('studio.gui.messagebox.showerror', side_effect=lambda *a, **k: self.errors.append(a))
        self.error_patch.start()

    def tearDown(self):
        self.error_patch.stop()
        # Hủy callback poll trước khi phá Tcl interpreter.
        for identifier in self.root.tk.call('after', 'info'):
            self.root.after_cancel(identifier)
        self.root.destroy()
        self.temp.cleanup()

    def create(self):
        with patch('studio.gui.filedialog.askdirectory', return_value=str(self.folder)):
            self.app.actions[0].invoke()
        self.root.update()

    def test_buttons_import_save_edit_preview_worker(self):
        self.create()
        self.assertTrue((self.folder / 'du-an.json').exists())
        self.app.script.insert('1.0', 'Lời thoại có dấu tiếng Việt.')
        image = self.folder / 'nguồn.png'
        Image.new('RGB', (320, 180), '#F6F1E3').save(image)
        with patch('studio.gui.filedialog.askopenfilename', return_value=str(image)):
            self.app.add_image()
        self.app.duration.set('1,2')
        self.app.save()
        loaded = load_project(self.folder / 'du-an.json')
        self.assertEqual(loaded['scenes'][0]['script'], 'Lời thoại có dấu tiếng Việt.')
        self.assertEqual(loaded['scenes'][0]['durationMs'], 1200)
        self.app.start_render(True)
        deadline = time.monotonic()+90
        while self.app.busy and time.monotonic() < deadline:
            self.root.update()
            time.sleep(.02)
        self.assertFalse(self.app.busy)
        self.assertTrue(self.app.preview[0].exists())
        self.assertFalse(self.errors)
        with patch('studio.gui.os.startfile', create=True) as player:
            self.app.play_preview()
            player.assert_called_once()
        self.app.script.insert('end', ' Đã sửa.')
        with self.assertRaises(ValueError):
            self.app.play_preview()

    def test_scene_operations_and_srt_import(self):
        self.create()
        self.app.name.set('Một')
        self.app.add_scene()
        self.app.name.set('Hai')
        self.app.move_scene(-1)
        self.assertEqual(self.app.project['scenes'][0]['name'], 'Hai')
        script = self.folder / 'phụ đề.srt'
        script.write_text('1\n00:00:00,000 --> 00:00:02,000\nXin chào!\n', encoding='utf-8-sig')
        with patch('studio.gui.filedialog.askopenfilename', return_value=str(script)):
            self.app.import_script()
        self.assertEqual(self.app.project['scenes'][-1]['script'], 'Xin chào!')
        with patch('studio.gui.messagebox.askyesno', return_value=True):
            self.app.delete_scene()
        self.assertEqual(len(self.app.project['scenes']), 2)
        self.assertFalse(self.errors)

    def test_required_vietnamese_buttons_and_no_project_error(self):
        labels = {button.cget('text') for button in self.app.actions}
        self.assertTrue({'Tạo dự án mới', 'Nhập kịch bản', 'Thêm hình ảnh', 'Thêm giọng đọc', 'Tạo video', 'Xem trước', 'Xuất MP4'}.issubset(labels))
        self.app.guard(self.app.add_image)
        self.assertEqual(len(self.errors), 1)

    def test_add_voice_and_export_from_gui(self):
        self.create()
        image = self.folder / 'ảnh.png'
        Image.new('RGB', (320, 180), '#F6F1E3').save(image)
        with patch('studio.gui.filedialog.askopenfilename', return_value=str(image)):
            self.app.add_image()
        voice = self.folder / 'giọng.wav'
        with wave.open(str(voice), 'wb') as out:
            out.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
            out.writeframes(b'\0\0'*16000)
        with patch('studio.gui.filedialog.askopenfilename', return_value=str(voice)):
            self.app.add_audio()
        self.assertTrue(self.app.current()['audio'].startswith('media/'))
        self.assertLess(abs(self.app.current()['durationMs']-1000), 34)
        self.app.aspect.set('9:16')
        target = self.folder / 'xuất từ giao diện.mp4'
        with patch('studio.gui.filedialog.asksaveasfilename', return_value=str(target)):
            self.app.start_render(False)
        deadline = time.monotonic()+90
        while self.app.busy and time.monotonic() < deadline:
            self.root.update()
            time.sleep(.02)
        self.assertFalse(self.app.busy)
        self.assertFalse(self.errors)
        import av
        with av.open(str(target)) as result:
            self.assertEqual((result.streams.video[0].width, result.streams.video[0].height), (1080, 1920))
            self.assertTrue(result.streams.audio)


if __name__ == '__main__':
    unittest.main()
