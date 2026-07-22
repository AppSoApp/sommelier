def median_lower(values):
    if not values:
        raise ValueError('values must not be empty')
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    else:
        return s[n // 2 - 1]
