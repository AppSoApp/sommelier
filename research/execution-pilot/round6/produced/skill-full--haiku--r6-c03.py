def vending_change_state(state, event):
    states = {"idle", "has_credit", "dispensing"}
    events = {"insert_coin", "select", "collect"}
    if state not in states:
        raise ValueError("invalid state")
    if event not in events:
        raise ValueError("invalid event")
    if state == "idle":
        return "has_credit" if event == "insert_coin" else "idle"
    if state == "has_credit":
        if event == "insert_coin":
            return "has_credit"
        if event == "select":
            return "dispensing"
        return "has_credit"
    if event == "collect":
        return "idle"
    return "dispensing"
