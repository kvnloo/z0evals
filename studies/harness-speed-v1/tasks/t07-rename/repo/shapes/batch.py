from shapes import geometry

def total(items):
    return sum(geometry.calc_area(kind, size) for kind, size in items)
