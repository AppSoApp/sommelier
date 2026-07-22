def find_min_rotated(nums):
    if not nums:
        raise ValueError('empty array')
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        else:
            hi = mid
    return nums[lo]


# Bug found in the original "battle-tested" version: it used `while lo <= hi`.
# Once lo == hi, mid == hi too, so `nums[mid] > nums[hi]` compares an element
# to itself and is always False -> the else branch sets hi = mid, which is
# already hi's value. Nothing changes, lo <= hi stays true, and the loop
# never terminates. This isn't just an edge case: EVERY input eventually
# converges to lo == hi (that's how the search finishes), so the original
# hangs forever on essentially all inputs, starting with the very first
# iteration for a single-element list. Fix: loop while lo < hi and return
# nums[lo] once the pointers meet.
assert find_min_rotated([1]) == 1                      # single element (old code hangs here)
assert find_min_rotated([1, 2, 3, 4, 5]) == 1           # zero rotation
assert find_min_rotated([2, 3, 4, 5, 1]) == 1           # rotated by len-1
assert find_min_rotated([-2, -1, -5, -4, -3]) == -5     # negatives
try:
    find_min_rotated([])
    raise AssertionError('expected ValueError on empty input')
except ValueError:
    pass
