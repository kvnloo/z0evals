import re


def words(text):
    return re.findall(r"[A-Za-z']+", text)
