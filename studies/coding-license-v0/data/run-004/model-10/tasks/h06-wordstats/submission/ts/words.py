def words(text):
    """Split text into words.

    A word is a run of letters and apostrophes. Leading and trailing
    apostrophes are stripped, and empty results are dropped.
    """
    result = []
    run = []
    for char in text:
        if char.isalpha() or char == "'":
            run.append(char)
        elif run:
            word = "".join(run).strip("'")
            if word:
                result.append(word)
            run.clear()
    word = "".join(run).strip("'")
    if word:
        result.append(word)
    return result


def load_stopwords(path):
    """Read a stopword file (one word per line).

    Blank lines and lines starting with '#' are ignored.
    """
    result = set()
    with open(path) as f:
        for line in f:
            entry = line.strip()
            if not entry or entry.startswith("#"):
                continue
            result.add(entry)
    return result
