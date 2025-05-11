import os
import sqlite3
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import re
import tempfile
import logging


def sanitize_filename(name):
    if not name:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9-_ ]", "", str(name)).replace(" ", "_")


def export_phrases(
    db_path,
    output_dir,
    date_vars,
    book,
    filters_shown,
    per_book=False,
    per_date=False,
    is_preview=False,
    custom_folder_name=None,
    user_timezone=None,
    include_tags=True,
):
    logging.basicConfig(
        level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    target_dir = (
        os.path.join(tempfile.gettempdir(), "vocab_builder_cache")
        if is_preview
        else output_dir
    )
    os.makedirs(target_dir, exist_ok=True)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        selected_dates = [d for d, var in date_vars.items() if var.get() == 1]
        filters = []
        params = []

        if selected_dates:
            if len(selected_dates) == len(date_vars):
                selected_dates = []
            else:
                date_conditions = []
                for date in selected_dates:
                    start = datetime.strptime(date, "%Y-%m-%d").replace(
                        tzinfo=user_timezone
                    )
                    end = (start + timedelta(days=1)).replace(tzinfo=user_timezone)
                    date_conditions.append("(a.create_time >= ? AND a.create_time < ?)")
                    params.extend([int(start.timestamp()), int(end.timestamp())])
                filters.append("(" + " OR ".join(date_conditions) + ")")

        if book and book != "(All)":
            filters.append("b.name = ?")
            params.append(book)

        query = """
            SELECT
                b.name AS book,
                a.word,
                REPLACE(a.prev_context || '==' || COALESCE(a.highlight, a.word) || '==' || a.next_context, CHAR(10), '<br>') AS phrase,
                a.create_time AS timestamp
            FROM vocabulary AS a
            LEFT JOIN title AS b ON a.title_id = b.id
        """
        if filters:
            query += " WHERE " + " AND ".join(filters)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        grouped = defaultdict(list)

        for book_val, word, phrase, timestamp in rows:
            if timestamp is None:
                continue
            book_val = book_val or "Unknown Book"
            word = word or "Unknown Word"
            phrase = phrase or "No context available"
            local_date = (
                datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
                .astimezone(user_timezone)
                .date()
                .isoformat()
            )
            if not selected_dates or local_date in selected_dates:
                key = ()
                if per_book:
                    key += (book_val,)
                if per_date:
                    key += (local_date,)
                grouped[key].append((book_val, word, phrase, local_date))

        written_files = []
        for key, entries in grouped.items():
            book_names = sorted(set(entry[0] for entry in entries if entry[0]))
            date_values = sorted(set(entry[3] for entry in entries if entry[3]))

            markdown = ""
            if include_tags:
                markdown += "---\n"
                markdown += "tags:\n  - english-learning\n  - reading\n"
                markdown += "book:\n"
                for b in book_names:
                    markdown += f'  - "{b}"\n'
                markdown += f"dates: {', '.join(date_values)}\n"
                markdown += "pages:\n---\n"

            current_book = None
            for book_val, word, phrase, _ in entries:
                if not per_book and book_val != current_book:
                    markdown += f"\n# {book_val}\n"
                    current_book = book_val
                markdown += f"## {word}\n> [!note] Context\n> {phrase}\n"

            if per_book and per_date:
                folder = os.path.join(target_dir, sanitize_filename(book_names[0]))
                filename = (
                    f"{sanitize_filename(date_values[0])}.md"
                    if len(date_values) == 1
                    else "vocabulary_builder.md"
                )
            elif per_date and custom_folder_name:
                folder = os.path.join(target_dir, custom_folder_name)
                filename = (
                    f"{sanitize_filename(date_values[0])}.md"
                    if len(date_values) == 1
                    else "vocabulary_builder.md"
                )
            elif per_book:
                folder = os.path.join(target_dir, sanitize_filename(book_names[0]))
                filename = f"{sanitize_filename(book_names[0])}.md"
            elif per_date:
                folder = os.path.join(target_dir, "by_date")
                filename = (
                    f"{sanitize_filename(date_values[0])}.md"
                    if len(date_values) == 1
                    else "vocabulary_builder.md"
                )
            else:
                folder = target_dir
                filename = "vocabulary_builder.md"

            os.makedirs(folder, exist_ok=True)
            filepath = os.path.join(folder, filename)
            written_files.append(filepath)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown)

        conn.close()
        return sorted(written_files), None

    except Exception as e:
        logging.error("Error in export_phrases", exc_info=True)
        return None, str(e)
