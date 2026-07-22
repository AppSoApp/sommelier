def caesar_shift_lower(text, shift):
    shift %= 26
    out = []
    for ch in text:
        if 'a' <= ch <= 'z':
            out.append(chr((ord(ch) - ord('a') + shift) % 26 + ord('a')))
        else:
            out.append(ch)
    return ''.join(out)
