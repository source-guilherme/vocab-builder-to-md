import ttkbootstrap as ttk
import atexit
from src.ui import SQLitePhraseExporter

if __name__ == "__main__":
    root = ttk.Window(themename="darkly")
    app = SQLitePhraseExporter(root)
    atexit.register(app.cleanup_cache)
    root.mainloop()
