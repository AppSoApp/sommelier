def manhattan_path_length(path):
    total = 0
    for i in range(1, len(path)):
        (x1, y1) = path[i - 1]
        (x2, y2) = path[i]
        total += abs(x2 - x1) + abs(y2 - y1)
    return total
