import csv, io
def total_by_category(csv_text):
    totals = {}
    rows = csv.reader(io.StringIO(csv_text))
    next(rows, None)
    for row in rows:
        if not row: continue
        totals[row[0]] = totals.get(row[0], 0.0) + float(row[1])
    return totals
