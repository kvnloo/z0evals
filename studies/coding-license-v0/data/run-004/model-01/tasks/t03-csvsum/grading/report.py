def total_by_category(csv_text):
    """csv_text has a header row `category,amount`. Return {category: total_amount}
    with amounts as floats. Fields may be quoted and quoted fields may contain commas."""
    import csv
    import io
    totals = {}
    reader = csv.reader(io.StringIO(csv_text))
    next(reader, None)  # skip the header row
    for row in reader:
        if not row:
            continue
        category, amount = row[0], row[1]
        totals[category] = totals.get(category, 0.0) + float(amount)
    return totals
