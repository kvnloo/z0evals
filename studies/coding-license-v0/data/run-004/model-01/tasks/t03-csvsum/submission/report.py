def total_by_category(csv_text):
    """csv_text has a header row `category,amount`. Return {category: total_amount}
    with amounts as floats. Fields may be quoted and quoted fields may contain commas."""
    totals = {}
    for line in csv_text.strip().splitlines()[1:]:
        category, amount = line.split(",")
        totals[category] = totals.get(category, 0.0) + float(amount)
    return totals
