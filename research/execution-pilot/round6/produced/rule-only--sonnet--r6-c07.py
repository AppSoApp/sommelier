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


# Evidence: original code used `s2 <= e1`, which wrongly counted merely-touching
# bookings (shared boundary point only) as conflicts. Fixed to strict `<`.
assert count_booking_conflicts([]) == 0
assert count_booking_conflicts([[0, 5]]) == 0
assert count_booking_conflicts([[0, 5], [5, 10]]) == 0        # touching only, not a conflict
assert count_booking_conflicts([[-5, 0], [0, 5]]) == 0        # negative touching, not a conflict
assert count_booking_conflicts([[0, 5], [0, 5]]) == 1         # identical bookings DO conflict
assert count_booking_conflicts([[0, 5], [3, 8]]) == 1         # real overlap
assert count_booking_conflicts([[-10, -3], [-5, -1]]) == 1    # negative real overlap
