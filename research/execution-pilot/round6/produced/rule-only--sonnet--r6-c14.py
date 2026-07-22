def caesar_shift_lower(text, shift):
    shift %= 26
    out = []
    for ch in text:
        if 'a' <= ch <= 'z':
            out.append(chr((ord(ch) - ord('a') + shift) % 26 + ord('a')))
        else:
            out.append(ch)
    return ''.join(out)


assert caesar_shift_lower('', 5) == ''
assert caesar_shift_lower('a', 0) == 'a'
assert caesar_shift_lower('a', 1) == 'b'
assert caesar_shift_lower('a', -1) == 'z'
assert caesar_shift_lower('abc', 26) == 'abc'
assert caesar_shift_lower('Hello, World! 123', 3) == 'Hhoor, Wruog! 123'
assert caesar_shift_lower('xyz', 3) == 'abc'
