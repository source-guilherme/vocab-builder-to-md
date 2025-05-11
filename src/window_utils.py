import os
import sys


def get_icon_path():
    # Try both PyInstaller and normal run locations
    if hasattr(sys, "_MEIPASS"):
        # Try icon in root of bundle
        icon_path = os.path.join(sys._MEIPASS, "icon.ico")
        if os.path.exists(icon_path):
            return icon_path
        # Try icon in src/ (for --add-data "src/icon.ico;src")
        icon_path = os.path.join(sys._MEIPASS, "src", "icon.ico")
        if os.path.exists(icon_path):
            return icon_path
    # Fallback to source tree
    here = os.path.dirname(__file__)
    icon_path = os.path.join(here, "icon.ico")
    if os.path.exists(icon_path):
        return icon_path
    icon_path = os.path.join(here, "src", "icon.ico")
    return icon_path


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
