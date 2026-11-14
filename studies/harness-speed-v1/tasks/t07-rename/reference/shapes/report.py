from shapes.geometry import area
def describe(kind, size):
    return f"{kind} area {area(kind, size):.2f}"
