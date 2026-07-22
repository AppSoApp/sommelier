def max_window_sum(nums, k):
    n = len(nums)
    if k <= 0 or k > n:
        raise ValueError("invalid window size")
    window = sum(nums[:k])
    best = window
    for i in range(k, n):
        window += nums[i] - nums[i - k]
        best = max(best, window)
    return best
