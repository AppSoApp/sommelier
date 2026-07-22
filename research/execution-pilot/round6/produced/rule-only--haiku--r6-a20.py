def isbn10_checksum_valid(isbn):
    cleaned = isbn.replace('-', '')
    if len(cleaned) != 10:
        return False
    if not cleaned[:9].isdigit():
        return False
    last = cleaned[9]
    if not (last.isdigit() or last == 'X'):
        return False
    total = 0
    for (i, ch) in enumerate(cleaned):
        val = 10 if ch == 'X' else int(ch)
        total += val * (i + 1)
    return total % 11 == 0
