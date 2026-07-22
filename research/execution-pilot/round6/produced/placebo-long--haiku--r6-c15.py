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
