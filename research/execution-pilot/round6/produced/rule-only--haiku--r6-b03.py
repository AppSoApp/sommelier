def chunk_list(items, n):
    if n <= 0:
        raise ValueError('n must be positive')
    return [items[i:i+n] for i in range(0, len(items), n)]


# Asserts proving correctness
assert chunk_list([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
assert chunk_list([1, 2, 3, 4, 5, 6], 2) == [[1, 2], [3, 4], [5, 6]]
assert chunk_list([], 2) == []
assert chunk_list([1, 2], 5) == [[1, 2]]
assert chunk_list([1], 1) == [[1]]
assert chunk_list([1, 2, 3], 1) == [[1], [2], [3]]
assert chunk_list([1, 2, 3, 4], 3) == [[1, 2, 3], [4]]

try:
    chunk_list([1, 2], 0)
    assert False, "Should raise ValueError for n=0"
except ValueError:
    pass

try:
    chunk_list([1, 2], -1)
    assert False, "Should raise ValueError for n=-1"
except ValueError:
    pass
