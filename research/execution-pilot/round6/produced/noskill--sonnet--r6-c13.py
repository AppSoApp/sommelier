def int_to_base_n(n, base):
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    if base < 2 or base > 36:
        raise ValueError("invalid base")
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return "0"
    out = []
    while n > 0:
        out.append(digits[n % base])
        n //= base
    return "".join(reversed(out))
