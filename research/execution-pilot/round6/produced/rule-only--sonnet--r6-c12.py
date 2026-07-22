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


# Bug found in the "double-checked" original: the length guard read
# `if abs(la - lb) >= 1: return False`, which rejects every pair of
# strings whose lengths differ at all (>=1), making the insertion/
# deletion branch below unreachable and breaking the length-diff-by-1
# case entirely (e.g. it returned False for "" vs "a", or "cat" vs
# "cats"). Corrected to `>= 2`, since a length gap of exactly 1 is
# still within one edit. Verified against 0/1/empty/negative-style
# edge cases:
assert is_one_edit_apart("", "") is True         # empty vs empty (distance 0)
assert is_one_edit_apart("", "a") is True         # empty vs 1-char (one insertion)
assert is_one_edit_apart("a", "") is True         # 1-char vs empty (one deletion)
assert is_one_edit_apart("", "ab") is False       # length gap of 2 -> not one edit
assert is_one_edit_apart("a", "a") is True        # single char, identical
assert is_one_edit_apart("a", "b") is True        # single char, substitution
assert is_one_edit_apart("cat", "cats") is True   # insertion at end
assert is_one_edit_apart("cats", "cat") is True   # deletion at end
assert is_one_edit_apart("abc", "abcd") is True   # length +1, insertion
assert is_one_edit_apart("abcdef", "abc") is False  # length gap of 3
