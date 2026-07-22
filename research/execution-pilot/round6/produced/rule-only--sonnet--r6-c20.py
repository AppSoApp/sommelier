def bitonic_peak_index(nums):
    if len(nums) < 3:
        raise ValueError('array must have at least 3 elements')
    peak = 0
    for i in range(1, len(nums)):
        if nums[i] > nums[peak]:
            peak = i
    return peak


# Evidence the "certified" version was wrong (used `<= 3`, rejecting valid
# len==3 mountains) and that this fix is correct on the boundary/edge cases:
for _bad in ([], [1], [1, 2]):
    try:
        bitonic_peak_index(_bad)
        assert False, f"expected ValueError for {_bad}"
    except ValueError:
        pass
assert bitonic_peak_index([1, 3, 2]) == 1          # len==3 must work, not raise
assert bitonic_peak_index([-1, -2, -3, -4]) == 0   # all-decreasing, negatives
assert bitonic_peak_index([-4, -3, -2, -1]) == 3   # all-increasing, negatives
assert bitonic_peak_index([1, 3, 5, 4, 2]) == 2    # true mountain peak
