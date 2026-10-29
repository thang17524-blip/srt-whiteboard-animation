"""Kiểm tra thư viện, Tcl/Tk, H.264, AAC và FFmpeg — không cài đặt tự động."""
import subprocess
import sys


def main():
    try:
        import tkinter as tk
        import av
        import cv2
        import numpy
        from PIL import Image
        from video_io import ffmpeg_path
        root = tk.Tk()
        root.withdraw()
        root.update()
        root.destroy()
        av.codec.Codec('libx264', 'w')
        av.codec.Codec('aac', 'w')
        subprocess.run([ffmpeg_path(), '-version'], check=True, stdout=subprocess.DEVNULL,
                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        print(f'Đạt: Python {sys.version.split()[0]}, Tk, OpenCV, NumPy, Pillow, PyAV, H.264, AAC và FFmpeg.')
        print('Mở chay_windows.cmd để sử dụng giao diện tiếng Việt.')
        return 0
    except Exception as exc:
        print(f'Chưa đạt: {exc}\nHãy chạy cai_dat_windows.cmd và đọc HUONG_DAN_WINDOWS.md.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
