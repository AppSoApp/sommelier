def manhattan_path_length(path):
    total = 0
    for i in range(len(path) - 1):
        (x1, y1) = path[i]
        (x2, y2) = path[i + 1]
        total += abs(x2 - x1) + abs(y2 - y1)
    return total
