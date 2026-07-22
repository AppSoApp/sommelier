def clamp_range(value, lo, hi):
    # If lo > hi (inverted range), swap them
    if lo > hi:
        lo, hi = hi, lo

    # Clamp value to [lo, hi]
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value
