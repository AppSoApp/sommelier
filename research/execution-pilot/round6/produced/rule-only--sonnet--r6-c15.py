def run_length_decode(s):
    (i, n) = (0, len(s))
    out = []
    while i < n:
        j = i
        while j < n and s[j].isdigit():
            j += 1
        if j == i:
            raise ValueError('expected digit count')
        count = int(s[i:j])
        if count <= 0:
            raise ValueError('count must be positive')
        if j >= n:
            raise ValueError('missing character after count')
        ch = s[j]
        if ch.isdigit():
            raise ValueError('character after count must not be a digit')
        out.append(ch * count)
        i = j + 1
    return ''.join(out)


assert run_length_decode('') == ''
assert run_length_decode('2a') == 'aa'
assert run_length_decode('1a') == 'a'
assert run_length_decode('10a') == 'a' * 10
assert run_length_decode('2a3a') == 'aaaaa'
assert run_length_decode('1a1b') == 'ab'
for bad in ('0a', '2', '22', 'ab', 'a2', '2a0b'):
    try:
        run_length_decode(bad)
    except ValueError:
        pass
    else:
        raise AssertionError(f'expected ValueError for {bad!r}')
