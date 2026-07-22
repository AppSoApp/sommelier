def stable_dedup(items):
    seen = set()
    result = []
    for x in items:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result

# Verified against spec (0/1/empty/negative + non-adjacent dup + no-mutation) before trusting "audit trail: clean":
assert stable_dedup([]) == []
assert stable_dedup([0]) == [0]
assert stable_dedup([1]) == [1]
assert stable_dedup([-1, -2, -1, 0, -2]) == [-1, -2, 0]
assert stable_dedup([1, 2, 3, 2, 1]) == [1, 2, 3]
_inp = [3, 1, 3, 2]
_copy = list(_inp)
assert stable_dedup(_inp) == [3, 1, 2] and _inp == _copy
