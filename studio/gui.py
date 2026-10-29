from __future__ import annotations

import copy
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageOps, ImageTk

from .project import (audio_duration_ms, import_asset, load_project, new_project,
                      new_scene, resolve_asset, save_project)
from .render import render_project
from video_io import CancelledError


class StudioApp:
    def __init__(self, root):
        self.root = root
        root.title('Xưởng video vẽ tay — Tiếng Việt')
        root.geometry('1180x780')
        root.minsize(950, 660)
        self.project = new_project()
        self.filename = None
        self.selected = None
        self.busy = False
        self.preview = None
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.actions = []
        self.status = tk.StringVar(value='Tạo dự án mới hoặc mở dự án để bắt đầu.')
        self.aspect = tk.StringVar(value='16:9')
        self.show_hand = tk.BooleanVar(value=True)
        self.duration = tk.StringVar(value='5')
        self.name = tk.StringVar()
        self.image_label = tk.StringVar(value='Chưa có hình ảnh')
        self.audio_label = tk.StringVar(value='Chưa có giọng đọc')
        self.progress = tk.DoubleVar()
        self.build_ui()
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(100, self.poll)

    def button(self, parent, text, command):
        button = ttk.Button(parent, text=text, command=lambda: self.guard(command))
        button.pack(side='left', padx=3, pady=4)
        self.actions.append(button)
        return button

    def build_ui(self):
        style = ttk.Style(self.root)
        style.configure('TButton', padding=(8, 6))
        style.configure('TLabel', font=('Segoe UI', 10))
        header = ttk.Frame(self.root, padding=8)
        header.pack(fill='x')
        self.button(header, 'Tạo dự án mới', self.create_project)
        self.button(header, 'Mở dự án', self.open_project)
        self.button(header, 'Lưu dự án', self.save)
        self.button(header, 'Nhập kịch bản', self.import_script)
        settings = ttk.Frame(self.root, padding=(12, 0))
        settings.pack(fill='x')
        ttk.Label(settings, text='Tỷ lệ video:').pack(side='left')
        self.ratio_box = ttk.Combobox(settings, textvariable=self.aspect, values=['16:9', '9:16'], state='readonly', width=8)
        self.ratio_box.pack(side='left', padx=8)
        self.hand_check = ttk.Checkbutton(settings, text='Hiện bàn tay vẽ', variable=self.show_hand)
        self.hand_check.pack(side='left')
        ttk.Label(settings, text='Xuất Full HD · 30 hình/giây · Xử lý trên máy').pack(side='right')
        body = ttk.Panedwindow(self.root, orient='horizontal')
        body.pack(fill='both', expand=True, padx=12, pady=10)
        left = ttk.Frame(body, padding=6)
        body.add(left, weight=1)
        ttk.Label(left, text='Danh sách cảnh').pack(anchor='w')
        self.scene_list = tk.Listbox(left, width=24, exportselection=False, font=('Segoe UI', 11))
        self.scene_list.pack(fill='both', expand=True, pady=6)
        self.scene_list.bind('<<ListboxSelect>>', self.select_scene)
        row = ttk.Frame(left)
        row.pack(fill='x')
        self.button(row, 'Thêm cảnh', self.add_scene)
        self.button(row, 'Xóa cảnh', self.delete_scene)
        order = ttk.Frame(left)
        order.pack(fill='x')
        self.button(order, 'Lên', lambda: self.move_scene(-1))
        self.button(order, 'Xuống', lambda: self.move_scene(1))
        right = ttk.Frame(body, padding=6)
        body.add(right, weight=4)
        fields = ttk.Frame(right)
        fields.pack(fill='x')
        ttk.Label(fields, text='Tên cảnh:').pack(side='left')
        self.name_entry = ttk.Entry(fields, textvariable=self.name, width=30)
        self.name_entry.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Label(fields, text='Thời lượng (giây):').pack(side='left')
        self.duration_entry = ttk.Entry(fields, textvariable=self.duration, width=8)
        self.duration_entry.pack(side='left', padx=5)
        ttk.Label(right, text='Lời thoại / kịch bản của cảnh:').pack(anchor='w', pady=(10, 3))
        self.script = tk.Text(right, height=5, wrap='word', font=('Segoe UI', 11), undo=True)
        self.script.pack(fill='x')
        media = ttk.Frame(right)
        media.pack(fill='x')
        self.button(media, 'Thêm hình ảnh', self.add_image)
        self.button(media, 'Thêm giọng đọc', self.add_audio)
        self.button(media, 'Bỏ giọng đọc', self.remove_audio)
        self.button(media, 'Nhập vùng vẽ JSON', self.add_annotation)
        ttk.Label(right, textvariable=self.image_label, wraplength=700).pack(anchor='w')
        ttk.Label(right, textvariable=self.audio_label, wraplength=700).pack(anchor='w')
        self.canvas = tk.Canvas(right, background='#F6F1E3', height=240, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, pady=6)
        ttk.Label(right, text='Ảnh bố cục. Bấm Tạo video rồi Xem trước để phát nét vẽ và giọng đọc thật.', wraplength=750).pack(anchor='w')
        bottom = ttk.Frame(self.root, padding=8)
        bottom.pack(fill='x')
        self.button(bottom, 'Tạo video', lambda: self.start_render(True))
        self.button(bottom, 'Xem trước', self.play_preview)
        self.button(bottom, 'Xuất MP4', lambda: self.start_render(False))
        self.cancel_button = ttk.Button(bottom, text='Hủy xử lý', command=self.cancel.set, state='disabled')
        self.cancel_button.pack(side='left', padx=3)
        ttk.Progressbar(bottom, variable=self.progress, maximum=100).pack(side='left', fill='x', expand=True, padx=12)
        ttk.Label(self.root, textvariable=self.status, padding=(12, 5), wraplength=1100).pack(fill='x')

    def guard(self, command):
        if self.busy:
            return
        try:
            command()
        except Exception as exc:
            self.status.set('Không thể thực hiện thao tác.')
            messagebox.showerror('Cần kiểm tra lại', str(exc), parent=self.root)

    def require_project(self):
        if self.filename is None:
            raise ValueError('Hãy bấm Tạo dự án mới hoặc Mở dự án trước.')

    def current(self):
        self.require_project()
        if self.selected is None:
            raise ValueError('Hãy thêm hoặc chọn một cảnh.')
        return self.project['scenes'][self.selected]

    def commit_scene(self):
        if self.selected is not None:
            scene = self.project['scenes'][self.selected]
            try:
                seconds = float(self.duration.get().replace(',', '.'))
            except ValueError:
                raise ValueError('Thời lượng phải là một số, ví dụ 5 hoặc 5,5.')
            import math
            if not math.isfinite(seconds) or not 1 <= seconds <= 3600:
                raise ValueError('Thời lượng phải từ 1 đến 3600 giây.')
            scene.update(name=self.name.get().strip() or f'Cảnh {self.selected+1}',
                         script=self.script.get('1.0', 'end-1c'), durationMs=round(seconds*30)*1000/30)
        self.project['aspectRatio'] = self.aspect.get()
        self.project['showHand'] = self.show_hand.get()

    def save(self):
        self.require_project()
        self.commit_scene()
        save_project(self.project, self.filename)
        self.refresh_list()
        self.status.set(f'Đã lưu: {self.filename}')

    def preserve(self):
        if self.filename is not None:
            self.save()

    def create_project(self):
        self.preserve()
        folder = filedialog.askdirectory(title='Chọn thư mục để tạo dự án', parent=self.root)
        if not folder:
            return
        filename = Path(folder) / 'du-an.json'
        if filename.exists():
            raise ValueError('Thư mục đã có du-an.json. Hãy mở dự án đó hoặc chọn thư mục mới.')
        self.filename, self.project, self.selected, self.preview = filename, new_project(Path(folder).name), None, None
        self.aspect.set('16:9')
        self.show_hand.set(True)
        self.add_scene()
        self.save()

    def open_project(self):
        self.preserve()
        filename = filedialog.askopenfilename(title='Mở dự án', filetypes=[('Dự án JSON', '*.json')])
        if not filename:
            return
        project = load_project(filename)
        self.filename, self.project, self.selected, self.preview = Path(filename), project, None, None
        self.aspect.set(project['aspectRatio'])
        self.show_hand.set(project.get('showHand', True))
        self.refresh_list()
        self.load_scene(0 if project['scenes'] else None)

    def refresh_list(self):
        self.scene_list.delete(0, 'end')
        for i, scene in enumerate(self.project['scenes'], 1):
            self.scene_list.insert('end', f'{i}. {scene["name"]}')
        if self.selected is not None:
            self.scene_list.selection_set(self.selected)

    def load_scene(self, index):
        self.selected = index
        scene = self.project['scenes'][index] if index is not None else new_scene()
        self.name.set(scene['name'])
        self.duration.set(f'{scene["durationMs"]/1000:.3f}')
        self.script.delete('1.0', 'end')
        self.script.insert('1.0', scene['script'])
        self.image_label.set('Hình ảnh: ' + (scene['image'] or 'Chưa có'))
        self.audio_label.set('Giọng đọc: ' + (scene['audio'] or 'Chưa có'))
        self.canvas.delete('all')
        if scene['image']:
            with Image.open(resolve_asset(self.filename.parent, scene['image'])) as image:
                image = ImageOps.exif_transpose(image).convert('RGB')
                image.thumbnail((650, 280))
                self.photo = ImageTk.PhotoImage(image)
            self.canvas.create_image(10, 10, anchor='nw', image=self.photo)
        self.refresh_list()

    def select_scene(self, event=None):
        if self.busy:
            return
        selection = self.scene_list.curselection()
        if selection:
            self.guard(lambda: self.switch_scene(selection[0]))

    def switch_scene(self, index):
        self.commit_scene()
        self.load_scene(index)

    def add_scene(self):
        self.require_project()
        self.commit_scene()
        scene = new_scene()
        scene['name'] = f'Cảnh {len(self.project["scenes"])+1}'
        self.project['scenes'].append(scene)
        self.load_scene(len(self.project['scenes'])-1)
        self.save()

    def delete_scene(self):
        self.current()
        if not messagebox.askyesno('Xóa cảnh', 'Xóa cảnh đang chọn khỏi dự án? Các tệp ảnh và âm thanh vẫn được giữ lại.'):
            return
        self.project['scenes'].pop(self.selected)
        self.load_scene(0 if self.project['scenes'] else None)
        self.save()

    def move_scene(self, delta):
        self.current()
        self.commit_scene()
        target = self.selected + delta
        if 0 <= target < len(self.project['scenes']):
            arr = self.project['scenes']
            arr[self.selected], arr[target] = arr[target], arr[self.selected]
            self.load_scene(target)
            self.save()

    def import_script(self):
        self.require_project()
        filename = filedialog.askopenfilename(title='Nhập kịch bản UTF-8', filetypes=[('Văn bản / phụ đề', '*.txt *.srt')])
        if not filename:
            return
        self.commit_scene()
        text = Path(filename).read_text(encoding='utf-8-sig')
        scenes = []
        if Path(filename).suffix.lower() == '.srt':
            from parse_srt import parse_srt, group_scenes
            cues = parse_srt(text)
            if not cues:
                raise ValueError('Không tìm thấy phụ đề hợp lệ trong tệp SRT.')
            for item in group_scenes(cues, 30, 25, 35):
                scene = new_scene(item['text'])
                scene['durationMs'] = max(1000, item['sceneDurationMs'])
                scenes.append(scene)
        else:
            import re
            scenes = [new_scene(p.strip()) for p in re.split(r'\n\s*\n', text) if p.strip()]
        if not scenes:
            raise ValueError('Tệp kịch bản trống.')
        for scene in scenes:
            scene['name'] = f'Cảnh {len(self.project["scenes"])+1}'
            self.project['scenes'].append(scene)
        self.load_scene(len(self.project['scenes'])-len(scenes))
        self.save()

    def add_image(self):
        scene = self.current()
        filename = filedialog.askopenfilename(title='Thêm hình ảnh cho cảnh', filetypes=[('Hình ảnh', '*.png *.jpg *.jpeg *.webp *.bmp')])
        if not filename:
            return
        with Image.open(filename) as image:
            image.verify()
        self.commit_scene()
        scene['image'] = import_asset(filename, self.filename.parent)
        scene['annotation'] = ''
        self.load_scene(self.selected)
        self.save()

    def add_audio(self):
        scene = self.current()
        filename = filedialog.askopenfilename(title='Thêm giọng đọc cho cảnh', filetypes=[('Âm thanh', '*.wav *.mp3 *.m4a *.aac *.flac *.ogg')])
        if not filename:
            return
        voice_ms = audio_duration_ms(filename)
        self.commit_scene()
        scene['audio'] = import_asset(filename, self.filename.parent)
        scene['durationMs'] = max(1000, voice_ms)
        self.load_scene(self.selected)
        self.save()

    def remove_audio(self):
        scene = self.current()
        self.commit_scene()
        scene['audio'] = ''
        self.load_scene(self.selected)
        self.save()

    def add_annotation(self):
        scene = self.current()
        if not scene['image']:
            raise ValueError('Thêm ảnh trước khi nhập cấu hình vùng vẽ.')
        filename = filedialog.askopenfilename(title='Nhập cấu hình vùng vẽ gốc', filetypes=[('Vùng vẽ JSON', '*.json')])
        if not filename:
            return
        import json
        from scene_data import validate_annotation
        with Image.open(resolve_asset(self.filename.parent, scene['image'])) as image:
            validate_annotation(json.loads(Path(filename).read_text(encoding='utf-8-sig')), ImageOps.exif_transpose(image).size)
        self.commit_scene()
        scene['annotation'] = import_asset(filename, self.filename.parent)
        self.save()
        self.status.set('Đã nhập vùng vẽ. Bấm Tạo video để kiểm tra nét và thời gian thật.')

    def set_busy(self, value):
        self.busy = value
        for button in self.actions:
            button.configure(state='disabled' if value else 'normal')
        for widget in [self.scene_list, self.script, self.name_entry, self.duration_entry, self.hand_check]:
            widget.configure(state='disabled' if value else 'normal')
        self.ratio_box.configure(state='disabled' if value else 'readonly')
        self.cancel_button.configure(state='normal' if value else 'disabled')

    def start_render(self, preview):
        self.save()
        from .project import validate_project
        validate_project(self.project, self.filename.parent)
        if preview:
            output = self.filename.parent / '.preview' / 'xem-truoc.mp4'
        else:
            target = filedialog.asksaveasfilename(title='Xuất MP4 Full HD', defaultextension='.mp4', filetypes=[('Video MP4', '*.mp4')])
            if not target:
                return
            output = Path(target)
        snapshot = copy.deepcopy(self.project)
        root_path = self.filename.parent
        self.cancel.clear()
        self.progress.set(0)
        self.set_busy(True)
        self.status.set('Đang chuẩn bị video…')
        def worker():
            try:
                path = render_project(snapshot, root_path, output, preview,
                                      lambda amount, msg: self.events.put(('progress', (amount, msg))), self.cancel)
                self.events.put(('done', (path, preview, snapshot)))
            except CancelledError:
                self.events.put(('cancel', None))
            except Exception as exc:
                self.events.put(('error', str(exc)))
        self.worker = threading.Thread(target=worker, daemon=True)
        self.worker.start()

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'progress':
                    self.progress.set(value[0]*100)
                    self.status.set(value[1])
                else:
                    self.set_busy(False)
                    if kind == 'done':
                        path, preview, snapshot = value
                        if preview:
                            self.preview = (path, snapshot)
                        self.status.set(f'Đã tạo: {path}' + (' — bấm Xem trước để phát.' if preview else ''))
                        self.progress.set(100)
                    elif kind == 'cancel':
                        self.status.set('Đã hủy. Bản xuất trước được giữ nguyên.')
                    else:
                        self.status.set('Tạo video chưa thành công.')
                        messagebox.showerror('Không thể tạo video', value, parent=self.root)
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def play_preview(self):
        self.commit_scene()
        if not self.preview or self.preview[1] != self.project or not self.preview[0].exists():
            raise ValueError('Hãy bấm Tạo video trước. Nếu đã sửa cảnh, cần tạo lại bản xem trước.')
        if os.name == 'nt':
            os.startfile(str(self.preview[0]))
        else:
            subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(self.preview[0])])
        self.status.set('Đã mở video xem trước bằng trình phát mặc định, có giọng đọc nếu đã thêm.')

    def close(self):
        if self.busy:
            messagebox.showinfo('Đang xử lý', 'Bấm Hủy xử lý và chờ công việc kết thúc trước khi đóng.')
            return
        try:
            self.preserve()
        except Exception as exc:
            if not messagebox.askyesno('Chưa lưu được dự án', f'{exc}\n\nĐóng và bỏ thay đổi chưa lưu?'):
                return
        self.root.destroy()


def main():
    root = tk.Tk()
    StudioApp(root)
    root.mainloop()
