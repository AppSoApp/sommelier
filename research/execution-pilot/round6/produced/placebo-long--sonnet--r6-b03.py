# verified against spec v2
def chunk_list(items, n):
    if n <= 0:
        raise ValueError('n must be positive')
    return [items[i:i + n] for i in range(0, len(items), n)]
