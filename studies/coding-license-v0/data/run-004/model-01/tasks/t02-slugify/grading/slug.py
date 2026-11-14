def slugify(text):
    """Lowercase ASCII slug: letters and digits kept, every run of other characters
    becomes a single '-', no leading or trailing '-'. Accented Latin letters are
    folded to their base letter (e.g. 'é' -> 'e'). Empty result -> 'n-a'."""
    raise NotImplementedError
