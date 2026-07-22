def run_length_encode(items):
    result = []
    for x in items:
        if result and result[-1][0] == x:
            result[-1][1] += 1
        else:
            result.append([x, 1])
    return result


assert run_length_encode([]) == []
assert run_length_encode([1]) == [[1, 1]]
assert run_length_encode([0]) == [[0, 1]]
assert run_length_encode([1, 1, 2]) == [[1, 2], [2, 1]]
assert run_length_encode([3, 3, 3]) == [[3, 3]]
assert run_length_encode([-1, -1, 2, -1]) == [[-1, 2], [2, 1], [-1, 1]]
