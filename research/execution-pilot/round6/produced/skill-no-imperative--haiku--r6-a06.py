def parse_key_value_pairs(s):
    result = {}
    for segment in s.split(';'):
        segment = segment.strip()
        if not segment:
            continue
        if '=' not in segment:
            continue
        key, value = segment.split('=', 1)
        result[key.strip()] = value.strip()
    return result
