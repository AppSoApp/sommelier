def mode_smallest(values):
    if not values:
        raise ValueError('values must not be empty')
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    best = None
    best_count = -1
    for v in sorted(counts):
        if counts[v] > best_count:
            best_count = counts[v]
            best = v
    return best
