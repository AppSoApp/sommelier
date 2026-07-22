def min_meeting_rooms(intervals):
    if not intervals:
        return 0
    starts = sorted((iv[0] for iv in intervals))
    ends = sorted((iv[1] for iv in intervals))
    rooms = 0
    max_rooms = 0
    i = j = 0
    n = len(intervals)
    while i < n and j < n:
        if starts[i] < ends[j]:
            rooms += 1
            max_rooms = max(max_rooms, rooms)
            i += 1
        else:
            rooms -= 1
            j += 1
    return max_rooms
