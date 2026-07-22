def split_bill_remainder(total_cents, n_people):
    base = total_cents // n_people
    remainder = total_cents % n_people
    result = []
    for i in range(n_people):
        result.append(base + 1 if i < remainder else base)
    return result
