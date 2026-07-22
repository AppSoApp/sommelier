def traffic_light_step(color, steps=1):
    order = {'red': 'green', 'green': 'yellow', 'yellow': 'red'}
    if color not in order:
        raise ValueError('invalid color')
    if steps < 0:
        raise ValueError('steps must be non-negative')
    for _ in range(steps):
        color = order[color]
    return color
