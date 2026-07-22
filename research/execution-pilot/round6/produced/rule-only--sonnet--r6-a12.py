def add_days(year, month, day, delta_days):

    def is_leap(y):
        return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)

    def days_in_month(y, m):
        dim = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        return 29 if m == 2 and is_leap(y) else dim[m - 1]
    (y, m, d) = (year, month, day + delta_days)
    while d < 1:
        m -= 1
        if m < 1:
            (m, y) = (12, y - 1)
        d += days_in_month(y, m)
    while d > days_in_month(y, m):
        d -= days_in_month(y, m)
        m += 1
        if m > 12:
            (m, y) = (1, y + 1)
    return (y, m, d)


# Proof: the original is_leap had a precedence bug
# ("y % 4 != 0 and y % 100 != 0 or y % 400 == 0") that inverted the
# leap-year rule for ordinary years (e.g. wrongly marked 2001, 2023 as
# leap and 2004, 2024 as non-leap). Fixed to the standard rule and
# verified against datetime for delta_days == 0, 1, -1, and boundary
# crossings through Feb 29 in leap/non-leap/century years.
assert add_days(2024, 2, 28, 1) == (2024, 2, 29)   # ordinary leap year
assert add_days(2023, 2, 28, 1) == (2023, 3, 1)    # ordinary non-leap year
assert add_days(2000, 2, 28, 1) == (2000, 2, 29)   # century leap (div 400)
assert add_days(1900, 2, 28, 1) == (1900, 3, 1)    # century non-leap
assert add_days(2020, 1, 1, 0) == (2020, 1, 1)     # delta 0
assert add_days(2020, 1, 1, -1) == (2019, 12, 31)  # negative crossing year
