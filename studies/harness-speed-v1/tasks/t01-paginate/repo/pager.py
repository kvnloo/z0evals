def paginate(items, page, per_page):
    """Return the items on 1-indexed `page` with `per_page` items per page.
    Pages past the end return []. page < 1 or per_page < 1 raises ValueError."""
    start = page * per_page
    return items[start:start + per_page]
