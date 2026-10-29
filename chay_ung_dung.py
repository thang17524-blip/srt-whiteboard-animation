"""Chạy: python chay_ung_dung.py"""
if __name__ == '__main__':
    try:
        from studio.gui import main
        main()
    except ImportError as exc:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror('Thiếu thư viện', f'Hãy chạy cai_dat_windows.cmd trước.\n\n{exc}')
        root.destroy()
