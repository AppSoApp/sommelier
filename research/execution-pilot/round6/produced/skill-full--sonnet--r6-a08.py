def tokenize_alnum_words(s):
    tokens = []
    current = []
    for ch in s:
        if ('a' <= ch <= 'z') or ('A' <= ch <= 'Z') or ('0' <= ch <= '9'):
            current.append(ch)
        elif current:
            tokens.append(''.join(current))
            current = []
    if current:
        tokens.append(''.join(current))
    return tokens
