from shapes.geometry import calc_area

def describe(kind, size):
    return f"{kind} area {calc_area(kind, size):.2f}"
