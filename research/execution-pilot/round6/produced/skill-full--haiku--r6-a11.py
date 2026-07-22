def minutes_between(start_hhmm, end_hhmm):
    (sh, sm) = start_hhmm.split(':')
    (eh, em) = end_hhmm.split(':')
    start_total = int(sh) * 60 + int(sm)
    end_total = int(eh) * 60 + int(em)
    diff = end_total - start_total
    if diff < 0:
        diff += 24 * 60
    return diff


# Boundary checks proving correctness
assert minutes_between("10:00", "10:00") == 0, "Equal times must return 0"
assert minutes_between("10:00", "11:00") == 60, "Forward same-day diff"
assert minutes_between("23:30", "00:15") == 45, "Wrap to next day"
assert minutes_between("00:00", "00:00") == 0, "Midnight boundary equal"
assert minutes_between("00:00", "23:59") == 1439, "Almost full day forward"
