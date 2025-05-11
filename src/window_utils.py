import os
import sys


def get_icon_path():
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "icon.ico")
    else:
        return os.path.join(os.path.dirname(__file__), "icon.ico")


def set_window_icon(window):
    try:
        window.iconbitmap(get_icon_path())
    except Exception:
        pass


def center_window(window):
    window.update_idletasks()
    w = window.winfo_width()
    h = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (w // 2)
    y = (window.winfo_screenheight() // 2) - (h // 2)
    window.geometry(f"+{x}+{y}")
