def int_to_roman_small(n):
    if n < 1 or n > 39:
        raise ValueError("n out of range 1..39")
    values = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    result = []
    for value, symbol in values:
        count, n = divmod(n, value)
        result.append(symbol * count)
    return "".join(result)
