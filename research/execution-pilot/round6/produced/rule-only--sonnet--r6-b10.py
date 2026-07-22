def manhattan_path_length(path):
    total = 0
    for i in range(1, len(path)):
        (x1, y1) = path[i - 1]
        (x2, y2) = path[i]
        total += abs(x2 - x1) + abs(y2 - y1)
    return total


assert manhattan_path_length([]) == 0
assert manhattan_path_length([(5, 5)]) == 0
assert manhattan_path_length([(0, 0), (0, 0)]) == 0
assert manhattan_path_length([(0, 0), (1, 1)]) == 2
assert manhattan_path_length([(-1, -1), (1, 1)]) == 4
assert manhattan_path_length([(0, 0), (3, 4), (3, 4), (0, 0)]) == 14
