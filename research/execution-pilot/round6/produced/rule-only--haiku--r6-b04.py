def top_k_with_ties(values, k):
    if k <= 0 or not values:
        return []
    order = sorted(range(len(values)), key=lambda i: (-values[i], i))
    chosen = order[:min(k, len(values))]
    return sorted(chosen)
