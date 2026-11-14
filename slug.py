import unicodedata


# Latin characters that do not decompose under NFKD but still have a base form.
_FOLD = str.maketrans({
    "æ": "ae",
    "œ": "oe",
    "ø": "o",
    "ł": "l",
    "đ": "d",
    "ð": "d",
    "þ": "th",
    "ħ": "h",
    "ŧ": "t",
    "ŋ": "n",
    "ı": "i",
    "ƒ": "f",
})


def slugify(text):
    """Lowercase ASCII slug: letters and digits kept, every run of other characters
    becomes a single '-', no leading or trailing '-'. Accented Latin letters are
    folded to their base letter (e.g. 'é' -> 'e'). Empty result -> 'n-a'."""
    folded = unicodedata.normalize("NFKD", text.casefold()).translate(_FOLD)

    chars = []
    pending_dash = False
    for char in folded:
        if unicodedata.combining(char):
            continue
        if char.isascii() and char.isalnum():
            if pending_dash and chars:
                chars.append("-")
            pending_dash = False
            chars.append(char)
        else:
            pending_dash = True

    return "".join(chars) or "n-a"