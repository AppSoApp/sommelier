def escape_delimiters(s):
    result = []
    for ch in s:
        if ch == '\\':
            result.append('\\\\')
        elif ch == '|':
            result.append('\\|')
        else:
            result.append(ch)
    return ''.join(result)
