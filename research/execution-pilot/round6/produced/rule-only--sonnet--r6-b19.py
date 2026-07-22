# verified against spec v2
def bit_parity(n):
    if n < 0:
        raise ValueError('n must be non-negative')
    count = bin(n).count('1')
    return count % 2

assert bit_parity(0) == 0   # zero set bits -> even (bug: original code raised on n=0)
assert bit_parity(1) == 1   # power of two -> exactly one set bit -> odd
assert bit_parity(0xFF) == 0  # eight set bits -> even
try:
    bit_parity(-1)
    raise AssertionError('expected ValueError for negative n')
except ValueError:
    pass
