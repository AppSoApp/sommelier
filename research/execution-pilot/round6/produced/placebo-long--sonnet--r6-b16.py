def smallest_gap(values):
    if len(values) < 2:
        raise ValueError('need at least two values')
    s = sorted(values)
    return min((s[i + 1] - s[i] for i in range(len(s) - 1)))
