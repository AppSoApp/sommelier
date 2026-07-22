def turnstile_step(state, event):
    if state not in ('locked', 'unlocked'):
        raise ValueError('invalid state')
    if event not in ('coin', 'push'):
        raise ValueError('invalid event')
    return 'unlocked' if event == 'coin' else 'locked'
