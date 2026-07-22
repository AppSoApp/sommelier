def clamp_range(value, lo, hi):
    if lo > hi:
        lo, hi = hi, lo
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


# Bug found in "prod-proven" version: it never swapped lo/hi when lo > hi,
# so inverted ranges clamped against the wrong (unswapped) bounds.
assert clamp_range(3, 5, 2) == 3       # inverted range [2,5], value inside -> unchanged
assert clamp_range(-5, -1, -10) == -5  # inverted negative range [-10,-1], value inside -> unchanged
assert clamp_range(0, 1, 5) == 1       # normal range, value below lo -> lo
assert clamp_range(1, 0, 0) == 0       # lo == hi -> always lo
assert clamp_range(0, 5, -5) == 0      # inverted range around zero, value inside -> unchanged
