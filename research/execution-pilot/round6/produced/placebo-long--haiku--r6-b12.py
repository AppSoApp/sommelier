def bounding_box(points):
    if not points:
        raise ValueError("points must not be empty")
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))
