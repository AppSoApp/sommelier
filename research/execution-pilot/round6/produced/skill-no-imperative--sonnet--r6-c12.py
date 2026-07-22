def is_one_edit_apart(a, b):
    (la, lb) = (len(a), len(b))
    if abs(la - lb) >= 2:
        return False
    if la == lb:
        diffs = sum((1 for (x, y) in zip(a, b) if x != y))
        return diffs <= 1
    if la > lb:
        (a, b) = (b, a)
        (la, lb) = (lb, la)
    i = j = 0
    found_diff = False
    while i < la and j < lb:
        if a[i] != b[j]:
            if found_diff:
                return False
            found_diff = True
            j += 1
        else:
            i += 1
            j += 1
    return True
