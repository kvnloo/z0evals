import math

def calc_area(kind, size):
    if kind == "square":
        return size * size
    if kind == "circle":
        return math.pi * size * size
    raise ValueError(kind)
