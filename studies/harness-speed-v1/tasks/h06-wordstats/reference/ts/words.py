import re


def words(text, ignore_case=False, min_length=1, stopwords=()):
    out = []
    stop = {s.lower() for s in stopwords} if ignore_case else set(stopwords)
    for raw in re.findall(r"[A-Za-z']+", text):
        w = raw.strip("'")
        if not w:
            continue
        if ignore_case:
            w = w.lower()
        if len(w) < min_length or w in stop:
            continue
        out.append(w)
    return out


def read_stopwords(path):
    with open(path) as f:
        return [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
