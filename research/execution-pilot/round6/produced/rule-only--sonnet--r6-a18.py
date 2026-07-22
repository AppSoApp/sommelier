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


# Original impl used str.isupper()/islower()/isdigit(), which accept non-ASCII
# Unicode characters (e.g. '²'.isdigit() -> True, 'İ'.isupper() -> True,
# 'ß'.islower() -> True) even though the spec restricts rules 2-4 to ASCII
# A-Z/a-z/0-9. Fixed with explicit ASCII range checks; asserts below prove it.
assert password_rule_count("") == 0
assert password_rule_count("a") == 1
assert password_rule_count("Aa1!aaaa") == 5
assert password_rule_count("²") == 0  # superscript two: not ASCII digit
assert password_rule_count("İ") == 0  # dotted capital I: not ASCII upper
assert password_rule_count("ß") == 0  # sharp s: not ASCII lower
assert password_rule_count("abcdefgh") == 2
assert password_rule_count("12345678") == 2
