def run_length_encode(items):
    result = []
    for x in items:
        if result and result[-1][0] == x:
            result[-1][1] += 1
        else:
            result.append([x, 1])
    return result
