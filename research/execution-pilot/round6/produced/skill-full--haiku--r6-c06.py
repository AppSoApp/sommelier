def free_slots(day_start, day_end, busy):
    if day_start >= day_end:
        return []
    ivs = sorted(((max(s, day_start), min(e, day_end)) for (s, e) in busy if max(s, day_start) < min(e, day_end)))
    gaps = []
    cursor = day_start
    for (s, e) in ivs:
        if s > cursor:
            gaps.append([cursor, s])
        cursor = max(cursor, e)
    if cursor < day_end:
        gaps.append([cursor, day_end])
    return gaps
