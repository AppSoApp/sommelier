def minutes_between(start_hhmm, end_hhmm):
    (sh, sm) = start_hhmm.split(':')
    (eh, em) = end_hhmm.split(':')
    start_total = int(sh) * 60 + int(sm)
    end_total = int(eh) * 60 + int(em)
    diff = end_total - start_total
    if diff < 0:
        diff += 24 * 60
    return diff
