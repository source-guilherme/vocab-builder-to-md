import os
import sqlite3
from datetime import datetime, timedelta, timezone
import ttkbootstrap as ttk
from ttkbootstrap.constants import W, NW, EW, BOTH
from tkinter import filedialog, Canvas, Frame, Scrollbar, messagebox
from tkinter.simpledialog import askstring
import tempfile
import shutil
import subprocess
import threading
from src.config import load_theme, save_theme
from src.exporter import export_phrases
from src.preview import show_preview
from src.window_utils import set_window_icon, center_window
import time


class SQLitePhraseExporter:
    def __init__(self, root):
        self.root = root
        self.root.title("Vocabulary Builder Exporter")
        self.root.resizable(False, False)

        set_window_icon(self.root)

        self.db_path = ""
        self.output_dir = ""
        self.date_vars = {}
        self.book_var = ttk.StringVar()
        self.filters_shown = False
        self.style = ttk.Style()
        self.selected_dates_cache = set()
        self.select_all_checked = False
        self.select_all_var = None
        self.include_tags_var = ttk.IntVar(value=1)

        self.load_theme()
        self.create_widgets()

    def set_icon_for_toplevel(self, toplevel):
        set_window_icon(toplevel)

    def load_theme(self):
        theme = load_theme()
        self.style.theme_use(theme)

    def save_theme(self, theme):
        save_theme(theme)

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=BOTH, expand=True)

        ttk.Button(
            frame, text="Browse Vocab Builder File", command=self.browse_db
        ).grid(row=0, column=0, padx=5, pady=5, sticky=W)
        self.db_label = ttk.Label(frame, text="No file selected", anchor="w")
        self.db_label.grid(row=0, column=1, sticky=EW)

        ttk.Button(frame, text="Select Output Folder", command=self.browse_output).grid(
            row=1, column=0, padx=5, pady=5, sticky=W
        )
        self.output_label = ttk.Label(frame, text="No folder selected", anchor="w")
        self.output_label.grid(row=1, column=1, sticky=EW)

        self.filter_btn = ttk.Button(
            frame, text="Show Filter Options", command=self.toggle_filters
        )
        self.filter_btn.grid(row=2, column=0, columnspan=2, pady=5)

        self.filter_frame = ttk.Frame(frame)

        ttk.Label(self.filter_frame, text="Choose a book to filter:").grid(
            row=0, column=0, sticky=W, padx=5
        )
        self.book_dropdown = ttk.Combobox(
            self.filter_frame, textvariable=self.book_var, state="readonly"
        )
        self.book_dropdown.bind(
            "<<ComboboxSelected>>", lambda e: self.populate_date_list()
        )
        self.book_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky=W)

        self.date_frame = ttk.Frame(self.filter_frame)
        self.date_toggle_btn = ttk.Button(
            self.filter_frame, text="Show Date Filter", command=self.toggle_date_frame
        )
        self.date_toggle_btn.grid(row=1, column=0, columnspan=2, sticky=W, padx=5)

        self.date_checkbox_frame = ttk.Frame(self.date_frame)
        self.date_checkbox_frame.grid(row=0, column=0, sticky=NW, padx=5, pady=5)

        self.export_per_book_var = ttk.IntVar(value=0)
        self.export_per_date_var = ttk.IntVar(value=0)

        ttk.Checkbutton(
            self.filter_frame,
            text="Export per book",
            variable=self.export_per_book_var,
            onvalue=1,
            offvalue=0,
        ).grid(row=99, column=0, columnspan=2, sticky=W, padx=5, pady=(5, 0))

        ttk.Checkbutton(
            self.filter_frame,
            text="Export per date",
            variable=self.export_per_date_var,
            onvalue=1,
            offvalue=0,
        ).grid(row=100, column=0, columnspan=2, sticky=W, padx=5)

        ttk.Checkbutton(
            self.filter_frame,
            text="Include Metadata",
            variable=self.include_tags_var,
            onvalue=1,
            offvalue=0,
        ).grid(row=101, column=0, columnspan=2, sticky=W, padx=5, pady=5)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=15)
        ttk.Button(
            button_frame, text="Preview Export", command=self.preview_export
        ).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Export!", command=self.perform_export).pack(
            side="left", padx=5
        )

        self.theme_var = ttk.StringVar(value=self.style.theme.name)
        ttk.Checkbutton(
            frame,
            text="Dark Mode",
            variable=self.theme_var,
            onvalue="darkly",
            offvalue="flatly",
            command=self.toggle_theme,
        ).grid(row=5, column=0, sticky=W, pady=5)

        frame.columnconfigure(1, weight=1)

    def toggle_theme(self):
        theme = self.theme_var.get()
        self.style.theme_use(theme)
        self.save_theme(theme)

    def toggle_filters(self):
        if self.filters_shown:
            self.reset_filters()
            self.filter_frame.grid_remove()
            self.filter_btn.config(text="Show Filter Options")
        else:
            self.filter_frame.grid(row=3, column=0, columnspan=2, sticky=EW)
            self.filter_btn.config(text="Hide Filter Options")
        self.filters_shown = not self.filters_shown

    def reset_filters(self):
        self.book_var.set("(All)")
        for var in self.date_vars.values():
            var.set(0)
        if self.select_all_var:
            self.select_all_var.set(0)
        self.selected_dates_cache.clear()
        self.select_all_checked = False
        self.export_per_book_var.set(0)
        self.export_per_date_var.set(0)
        self.include_tags_var.set(1)

        for widget in self.date_checkbox_frame.winfo_children():
            widget.destroy()
        self.date_vars.clear()

        self.date_frame.grid_remove()
        self.date_toggle_btn.config(text="Show Date Filter")

    def toggle_date_frame(self):
        if self.date_frame.winfo_ismapped():
            self.selected_dates_cache = {
                date for date, var in self.date_vars.items() if var.get() == 1
            }
            for var in self.date_vars.values():
                var.set(0)
            if self.select_all_var:
                self.select_all_checked = self.select_all_var.get() == 1
            else:
                self.select_all_checked = False
            self.date_frame.grid_remove()
            self.date_toggle_btn.config(text="Show Date Filter")
        else:
            self.date_frame.grid(row=2, column=0, columnspan=2, sticky="w")
            self.date_toggle_btn.config(text="Hide Date Filter")
            self.populate_date_list()

    def custom_messagebox(self, title, message, type="info"):
        top = ttk.Toplevel(self.root)
        top.title(title)
        top.resizable(False, False)

        set_window_icon(top)

        frame = ttk.Frame(top, padding=15)
        frame.pack(fill=BOTH, expand=True)

        icon_label = ttk.Label(frame)
        if type == "info":
            icon_label.config(text="ℹ️", font=("Arial", 24))
        elif type == "warning":
            icon_label.config(text="⚠️", font=("Arial", 24))
        elif type == "error":
            icon_label.config(text="❌", font=("Arial", 24))
        icon_label.grid(row=0, column=0, padx=10, pady=10, sticky="n")

        text_frame = ttk.Frame(frame)
        text_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        canvas = Canvas(text_frame, width=300, height=150)
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=canvas.yview)
        scrollable_text = ttk.Frame(canvas)

        scrollable_text.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_text, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        message_label = ttk.Label(
            scrollable_text,
            text=message,
            wraplength=280,
            anchor="w",
            justify="left",
            padding=(10, 10, 10, 10),
        )
        message_label.pack(fill="both", expand=True)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def update_scrollbar_visibility():
            canvas.update_idletasks()
            bbox = canvas.bbox("all")
            if bbox is not None:
                canvas.config(scrollregion=bbox)
                content_height = bbox[3] - bbox[1]
                visible_height = int(canvas.winfo_height())
                if content_height <= visible_height:
                    scrollbar.pack_forget()
                else:
                    scrollbar.pack(side="right", fill="y")

        canvas.bind("<Configure>", lambda e: update_scrollbar_visibility())
        scrollable_text.bind("<Configure>", lambda e: update_scrollbar_visibility())

        def _on_mousewheel(event):
            bbox = canvas.bbox("all")
            if bbox is None:
                return
            first, last = canvas.yview()
            if (event.delta > 0 and first <= 0) or (event.delta < 0 and last >= 1):
                return "break"
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"

        canvas.bind_all("<MouseWheel>", _on_mousewheel, add="+")
        canvas.bind_all(
            "<Button-4>", lambda e: canvas.yview_scroll(-1, "units"), add="+"
        )
        canvas.bind_all(
            "<Button-5>", lambda e: canvas.yview_scroll(1, "units"), add="+"
        )

        ok_button = ttk.Button(frame, text="OK", command=top.destroy)
        ok_button.grid(row=1, column=0, columnspan=2, pady=15)

        center_window(top)

        top.transient(self.root)
        top.grab_set()
        self.root.wait_window(top)

    def browse_db(self):
        path = filedialog.askopenfilename(filetypes=[("SQLite3 DB", "*.sqlite3 *.db")])
        if path:
            self.db_path = path
            self.db_label.config(text=os.path.basename(path))
            self.populate_date_list()
            self.populate_book_list()
        else:
            self.custom_messagebox(
                "No File Selected",
                "Please select a valid SQLite3 database file.",
                type="warning",
            )

    def browse_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_dir = folder
            self.output_label.config(text=folder)
        else:
            self.custom_messagebox(
                "No Folder Selected",
                "Please select a valid output folder.",
                type="warning",
            )

    def populate_date_list(self):
        for widget in self.date_checkbox_frame.winfo_children():
            widget.destroy()
        self.date_vars.clear()

        if not self.db_path:
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = """
                SELECT DISTINCT a.create_time
                FROM vocabulary a
                LEFT JOIN title b ON a.title_id = b.id
                WHERE a.create_time IS NOT NULL
            """
            params = []

            if self.book_var.get() and self.book_var.get() != "(All)":
                query += " AND b.name = ?"
                params.append(self.book_var.get())

            cursor.execute(query, params)
            timestamps = [row[0] for row in cursor.fetchall()]
            conn.close()

            date_set = sorted(
                set(
                    datetime.fromtimestamp(ts, tz=timezone.utc)
                    .astimezone()
                    .date()
                    .isoformat()
                    for ts in timestamps
                )
            )

            SCROLL_THRESHOLD = 10

            if len(date_set) > SCROLL_THRESHOLD:
                canvas = Canvas(self.date_checkbox_frame)
                scrollbar = Scrollbar(
                    self.date_checkbox_frame, orient="vertical", command=canvas.yview
                )
                scrollable_frame = Frame(canvas)

                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
                )
                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)

                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")
                parent_frame = scrollable_frame
            else:
                parent_frame = self.date_checkbox_frame

            self.select_all_var = ttk.IntVar(value=1 if self.select_all_checked else 0)
            self.select_all_cb = ttk.Checkbutton(
                parent_frame,
                text="Select All",
                variable=self.select_all_var,
                onvalue=1,
                offvalue=0,
                command=self.toggle_all_dates,
            )
            self.select_all_cb.pack(anchor="w")

            for d in date_set:
                var = ttk.IntVar(value=1 if d in self.selected_dates_cache else 0)
                cb = ttk.Checkbutton(
                    parent_frame,
                    text=d,
                    variable=var,
                    onvalue=1,
                    offvalue=0,
                    command=self.update_select_all_state,
                )
                cb.pack(anchor="w")
                self.date_vars[d] = var

        except Exception as e:
            self.custom_messagebox(
                "Date Load Error", f"Could not load dates:\n{e}", type="error"
            )

    def update_select_all_state(self):
        if self.select_all_var is not None:
            if all(var.get() == 1 for var in self.date_vars.values()):
                self.select_all_var.set(1)
                self.select_all_checked = True
            else:
                self.select_all_var.set(0)
                self.select_all_checked = False

    def toggle_all_dates(self):
        new_value = self.select_all_var.get()
        for var in self.date_vars.values():
            var.set(new_value)
        self.populate_book_list()

    def preview_export(self):
        if not self.db_path or not self.output_dir:
            self.custom_messagebox(
                "Missing Info",
                "Please select both a database and an output folder.",
                type="warning",
            )
            return

        offset_sec = -time.timezone
        offset_hours = offset_sec / 3600
        user_timezone = timezone(timedelta(hours=offset_hours))

        output_files, error = export_phrases(
            self.db_path,
            self.output_dir,
            self.date_vars,
            self.book_var.get(),
            self.filters_shown,
            per_book=self.export_per_book_var.get() == 1,
            per_date=self.export_per_date_var.get() == 1,
            is_preview=True,
            custom_folder_name=None,
            user_timezone=user_timezone,
            include_tags=self.include_tags_var.get() == 1,
        )

        if error:
            self.custom_messagebox(
                "Error", f"Failed to generate preview:\n{error}", type="error"
            )
        else:
            combined_preview = ""
            temp_files = []
            for file_path in sorted(output_files):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        combined_preview += f.read() + "\n\n"
                    temp_files.append(file_path)
                except Exception as e:
                    self.custom_messagebox(
                        "Error", f"Failed to read file {file_path}:\n{e}", type="error"
                    )
                    return

            def cleanup_temp_files():
                cache_dir = os.path.join(tempfile.gettempdir(), "vocab_builder_cache")
                try:
                    shutil.rmtree(cache_dir)
                except Exception as e:
                    print(f"Failed to delete cache folder {cache_dir}: {e}")

            show_preview(
                combined_preview, title="Markdown Preview", on_close=cleanup_temp_files
            )

    def perform_export(self):
        if not self.db_path or not self.output_dir:
            self.custom_messagebox(
                "Missing Info",
                "Please select both a database and an output folder.",
                type="warning",
            )
            return

        def export_task():
            folder_name = None
            if (
                self.export_per_date_var.get() == 1
                and not self.export_per_book_var.get() == 1
            ):
                folder_name = askstring(
                    "Folder Name", "Enter a folder name for date-based export:"
                )
                if not folder_name:
                    self.custom_messagebox(
                        "Missing Info",
                        "Folder name is required for date-based export.",
                        type="warning",
                    )
                    return

            offset_sec = -time.timezone
            offset_hours = offset_sec / 3600
            user_timezone = timezone(timedelta(hours=offset_hours))

            output_files, error = export_phrases(
                self.db_path,
                self.output_dir,
                self.date_vars,
                self.book_var.get(),
                self.filters_shown,
                per_book=self.export_per_book_var.get() == 1,
                per_date=self.export_per_date_var.get() == 1,
                is_preview=False,
                custom_folder_name=folder_name,
                user_timezone=user_timezone,
                include_tags=self.include_tags_var.get() == 1,
            )

            if error:
                self.custom_messagebox(
                    "Error", f"Failed to export data:\n{error}", type="error"
                )
            else:
                exported_files = "\n".join(output_files)
                self.custom_messagebox(
                    "Success", f"Vocabulary exported to:\n{exported_files}", type="info"
                )

                if messagebox.askyesno(
                    "Open Folder", "Do you want to open the output folder?"
                ):
                    try:
                        if os.name == "nt":
                            os.startfile(self.output_dir)
                        elif os.name == "posix":
                            subprocess.run(["xdg-open", self.output_dir], check=True)
                    except Exception as e:
                        self.custom_messagebox(
                            "Error", f"Failed to open folder:\n{e}", type="error"
                        )

        threading.Thread(target=export_task).start()

    def cleanup_cache(self):
        cache_dir = os.path.join(tempfile.gettempdir(), "vocab_builder_cache")
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
            except Exception as e:
                print(f"Failed to delete cache folder {cache_dir}: {e}")

    def populate_book_list(self):
        if not self.db_path:
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = """
                SELECT DISTINCT b.name
                FROM vocabulary a
                LEFT JOIN title b ON a.title_id = b.id
                WHERE b.name IS NOT NULL
            """
            params = []

            if self.date_vars and any(
                var.get() == 1 for var in self.date_vars.values()
            ):
                date_ranges = [
                    (
                        datetime.strptime(date_str, "%Y-%m-%d"),
                        datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1),
                    )
                    for date_str, var in self.date_vars.items()
                    if var.get() == 1
                ]
                sub_filters = []
                for start, end in date_ranges:
                    sub_filters.append("(a.create_time >= ? AND a.create_time < ?)")
                    params.extend([int(start.timestamp()), int(end.timestamp())])
                query += " AND (" + " OR ".join(sub_filters) + ")"

            cursor.execute(query, params)
            books = sorted([row[0] for row in cursor.fetchall()])
            conn.close()

            self.book_dropdown["values"] = ["(All)"] + books
            if self.book_var.get() not in books:
                self.book_dropdown.set("(All)")

        except Exception as e:
            self.custom_messagebox(
                "Book Load Error", f"Could not load books:\n{e}", type="error"
            )
