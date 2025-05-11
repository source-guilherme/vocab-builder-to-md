from datetime import datetime, timedelta

def build_date_filter(date_vars):
    selected_dates = [d for d, var in date_vars.items() if var.get() == 1]
    date_ranges = [
        (datetime.strptime(d, "%Y-%m-%d"), datetime.strptime(d, "%Y-%m-%d") + timedelta(days=1))
        for d in selected_dates
    ]
    conditions = []
    params = []
    for start, end in date_ranges:
        conditions.append("(a.create_time >= ? AND a.create_time < ?)")
        params.extend([int(start.timestamp()), int(end.timestamp())])
    return conditions, params

def build_book_filter(book_name):
    if book_name and book_name != "(All)":
        return "b.name = ?", [book_name]
    return None, []
