"""Ghi H.264 qua PyAV, kiểm tra hủy và tìm FFmpeg đi kèm gói cài."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import av


class CancelledError(Exception):
    pass


class VideoWriter:
    def __init__(self, path, width, height, fps, progress=None, cancel=None, total=1):
        self.container = av.open(str(path), mode='w', options={'movflags': '+faststart'})
        self.stream = self.container.add_stream('libx264', rate=fps)
        self.stream.width, self.stream.height = width, height
        self.stream.pix_fmt = 'yuv420p'
        self.stream.options = {'crf': '20', 'preset': 'veryfast'}
        self.progress, self.cancel, self.total = progress, cancel, total
        self.count = 0

    def write(self, image):
        if self.cancel is not None and self.cancel.is_set():
            raise CancelledError('Đã hủy tạo video.')
        frame = av.VideoFrame.from_ndarray(image, format='bgr24')
        frame.pts = self.count
        for packet in self.stream.encode(frame):
            self.container.mux(packet)
        self.count += 1
        if self.progress and self.count % 3 == 0:
            self.progress(min(1.0, self.count / max(1, self.total)))

    def release(self):
        try:
            for packet in self.stream.encode(None):
                self.container.mux(packet)
        finally:
            self.container.close()


def ffmpeg_path():
    configured = os.environ.get('WHITEBOARD_FFMPEG')
    if configured:
        if not Path(configured).is_file():
            raise ValueError('Đường dẫn WHITEBOARD_FFMPEG không tồn tại.')
        return configured
    system = shutil.which('ffmpeg')
    if system:
        return system
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError) as exc:
        raise RuntimeError('Thiếu FFmpeg. Hãy chạy cai_dat_windows.cmd hoặc cài imageio-ffmpeg.') from exc


def run_ffmpeg(arguments, cancel=None):
    import time
    import tempfile
    # Tệp nhật ký tránh đầy pipe khi bộ mã hóa phát nhiều thông báo lỗi.
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen([ffmpeg_path(), '-hide_banner', '-loglevel', 'error', '-y', *map(str, arguments)],
                                   stdout=subprocess.DEVNULL, stderr=log,
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            while process.poll() is None:
                if cancel is not None and cancel.is_set():
                    raise CancelledError('Đã hủy xử lý video.')
                time.sleep(0.1)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        if process.returncode:
            log.seek(0)
            raise RuntimeError('Không xử lý được video/âm thanh: ' + log.read().decode('utf-8', errors='replace')[-1800:])
