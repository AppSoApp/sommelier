def clamp_range(value, lo, hi):
    # If lo > hi (inverted range), swap them to get effective bounds
    if lo > hi:
        lo, hi = hi, lo

    if value < lo:
        return lo
    if value > hi:
        return hi
    return value
