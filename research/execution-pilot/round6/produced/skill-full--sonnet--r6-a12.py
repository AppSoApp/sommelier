def add_days(year, month, day, delta_days):

    def is_leap(y):
        return (y % 4 == 0 and y % 100 != 0) or y % 400 == 0

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
