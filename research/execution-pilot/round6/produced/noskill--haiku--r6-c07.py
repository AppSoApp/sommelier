def count_booking_conflicts(bookings):
    n = len(bookings)
    count = 0
    for i in range(n):
        (s1, e1) = bookings[i]
        for j in range(i + 1, n):
            (s2, e2) = bookings[j]
            if s1 < e2 and s2 < e1:
                count += 1
    return count
