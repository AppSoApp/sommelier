def password_rule_count(password):
    count = 0
    if len(password) >= 8:
        count += 1
    if any(c.isupper() for c in password):
        count += 1
    if any(c.islower() for c in password):
        count += 1
    if any(c.isdigit() for c in password):
        count += 1
    if any(c in "!@#$%^&*" for c in password):
        count += 1
    return count
