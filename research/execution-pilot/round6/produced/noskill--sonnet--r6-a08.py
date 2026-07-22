def tokenize_alnum_words(s):
    tokens = []
    current = []
    for ch in s:
        if ch.isalnum():
            current.append(ch)
        elif current:
            tokens.append(''.join(current))
            current = []
    if current:
        tokens.append(''.join(current))
    return tokens
