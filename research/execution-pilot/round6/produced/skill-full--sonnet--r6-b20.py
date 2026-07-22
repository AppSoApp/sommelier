def lowest_set_bit(n):
    if n <= 0:
        raise ValueError('n must be positive')
    return n & -n
