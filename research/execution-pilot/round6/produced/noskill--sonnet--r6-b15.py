# verified against spec v2
def trimmed_sum(values, k):
    if k < 0:
        raise ValueError('k must be non-negative')
    s = sorted(values)
    n = len(s)
    if 2 * k >= n:
        return 0
    return sum(s[k:n - k])
