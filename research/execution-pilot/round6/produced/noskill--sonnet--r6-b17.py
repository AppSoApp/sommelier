def popcount_range(a, b):
    if a < 0 or a > b:
        raise ValueError("invalid range")
    return sum(bin(n).count('1') for n in range(a, b + 1))
