def count_booking_conflicts(bookings):
    n = len(bookings)
    count = 0
    for i in range(n):
        (s1, e1) = bookings[i]
        for j in range(i + 1, n):
            (s2, e2) = bookings[j]
            if max(s1, s2) < min(e1, e2):
                count += 1
    return count
