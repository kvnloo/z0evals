def paginate(items, page, per_page):
    """Return the items on 1-indexed `page` with `per_page` items per page.
    Pages past the end return []. page < 1 or per_page < 1 raises ValueError."""
    if page < 1 or per_page < 1:
        raise ValueError("page and per_page must be >= 1")
    start = (page - 1) * per_page
    return items[start:start + per_page]
