def banker_round_cents(tenths_of_cent):
    (whole, rem) = divmod(tenths_of_cent, 10)
    if rem < 5:
        return whole
    if rem > 5:
        return whole + 1
    return whole if whole % 2 == 0 else whole + 1
