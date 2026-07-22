def lowest_set_bit(n):
    if n <= 0:
        raise ValueError('n must be positive')
    return n & -n

assert lowest_set_bit(1) == 1
assert lowest_set_bit(12) == 4
assert lowest_set_bit(1024) == 1024
