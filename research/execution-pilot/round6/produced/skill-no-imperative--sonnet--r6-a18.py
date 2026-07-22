def password_rule_count(password):
    count = 0
    if len(password) >= 8:
        count += 1
    if any('A' <= c <= 'Z' for c in password):
        count += 1
    if any('a' <= c <= 'z' for c in password):
        count += 1
    if any('0' <= c <= '9' for c in password):
        count += 1
    if any(c in "!@#$%^&*" for c in password):
        count += 1
    return count
