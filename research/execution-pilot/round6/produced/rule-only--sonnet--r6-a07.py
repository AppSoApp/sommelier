def is_balanced_brackets(s):
    pairs = {')': '(', ']': '[', '}': '{'}
    opens = set(pairs.values())
    stack = []
    for ch in s:
        if ch in opens:
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return len(stack) == 0


# Original "prod-proven since Q1" code inverted the pop comparison
# (`== pairs[ch]` instead of `!= pairs[ch]`), so it returned False on a
# *match* and accepted real mismatches. Probed on 0/1/empty/negative
# shapes before trusting it -- it failed the simplest balanced case.
assert is_balanced_brackets("") is True          # empty -> balanced
assert is_balanced_brackets("()") is True         # was returning False before fix
assert is_balanced_brackets("(") is False         # single open, unbalanced
assert is_balanced_brackets(")") is False         # single close, unbalanced
assert is_balanced_brackets("([)]") is False      # improperly nested (negative case)
assert is_balanced_brackets("a(b)[c]{d}e") is True  # non-bracket chars ignored
