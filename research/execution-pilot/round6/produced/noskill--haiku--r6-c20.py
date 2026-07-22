def bitonic_peak_index(nums):
    if len(nums) < 3:
        raise ValueError('array must have at least 3 elements')
    peak = 0
    for i in range(1, len(nums)):
        if nums[i] > nums[peak]:
            peak = i
    return peak
