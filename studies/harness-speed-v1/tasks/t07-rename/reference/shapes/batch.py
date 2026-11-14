from shapes import geometry
def total(items):
    return sum(geometry.area(kind, size) for kind, size in items)
