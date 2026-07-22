def kth_smallest_distinct(nums, k):
    if k < 1:
        raise ValueError('k must be >= 1')
    distinct = sorted(set(nums))
    if k > len(distinct):
        raise ValueError('k exceeds number of distinct values')
    return distinct[k - 1]
