import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from src.window_utils import set_window_icon, center_window


def show_preview(markdown_text, title="Markdown Preview", on_close=None):
    try:
        preview_window = tk.Toplevel()
        preview_window.title(title)
        preview_window.geometry("800x600")

        set_window_icon(preview_window)

        text_box = ScrolledText(preview_window, wrap="word")
        text_box.insert("1.0", markdown_text)
        text_box.config(state="disabled")
        text_box.pack(expand=True, fill="both")

        center_window(preview_window)

        if on_close:
            preview_window.protocol(
                "WM_DELETE_WINDOW", lambda: (on_close(), preview_window.destroy())
            )
    except Exception as e:
        print(f"Error displaying preview: {e}")
