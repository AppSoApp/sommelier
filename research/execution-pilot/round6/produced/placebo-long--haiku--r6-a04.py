def run_length_encode(s):
    if not s:
        return ''
    result = []
    prev = s[0]
    count = 1
    for ch in s[1:]:
        if ch == prev:
            count += 1
        else:
            result.append(str(count) + prev)
            prev = ch
            count = 1
    result.append(str(count) + prev)
    return ''.join(result)
