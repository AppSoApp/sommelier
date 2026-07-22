def garage_door_step(state, event):
    valid_states = {'closed', 'open', 'moving_up', 'moving_down'}
    valid_events = {'press', 'obstacle', 'done'}
    if state not in valid_states:
        raise ValueError('invalid state')
    if event not in valid_events:
        raise ValueError('invalid event')
    table = {('closed', 'press'): 'moving_up', ('moving_up', 'done'): 'open', ('moving_up', 'obstacle'): 'moving_down', ('open', 'press'): 'moving_down', ('moving_down', 'done'): 'closed', ('moving_down', 'obstacle'): 'moving_up'}
    return table.get((state, event), state)
