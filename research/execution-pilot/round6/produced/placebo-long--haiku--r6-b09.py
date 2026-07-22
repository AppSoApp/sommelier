def rect_overlap_area(a, b):
    (ax1, ay1, ax2, ay2) = a
    (bx1, by1, bx2, by2) = b
    ox1 = max(ax1, bx1)
    oy1 = max(ay1, by1)
    ox2 = min(ax2, bx2)
    oy2 = min(ay2, by2)
    w = ox2 - ox1
    h = oy2 - oy1
    if w <= 0 or h <= 0:
        return 0
    return w * h
