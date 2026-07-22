def day_of_year(year, month, day):
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    leap = (year % 4 == 0) and (year % 100 != 0 or year % 400 == 0)
    if leap:
        days_in_month[1] = 29
    return sum(days_in_month[:month - 1]) + day
