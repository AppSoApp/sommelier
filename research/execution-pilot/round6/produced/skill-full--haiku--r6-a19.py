def clamp_range(value, lo, hi):
    if lo > hi:
        lo, hi = hi, lo

    if value < lo:
        return lo
    if value > hi:
        return hi
    return value
