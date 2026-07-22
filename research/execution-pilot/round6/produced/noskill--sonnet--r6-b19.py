def bit_parity(n):
    if n < 0:
        raise ValueError('n must be non-negative')
    count = bin(n).count('1')
    return count % 2
