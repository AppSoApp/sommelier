def leftmost_insertion_index(sorted_list, target):
    for (i, v) in enumerate(sorted_list):
        if v >= target:
            return i
    return len(sorted_list)
