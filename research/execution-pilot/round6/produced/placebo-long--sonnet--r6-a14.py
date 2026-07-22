def tiered_fee(amount_cents):
    if amount_cents <= 0:
        return 0
    tier1 = min(amount_cents, 10000)
    tier2 = max(0, min(amount_cents, 50000) - 10000)
    tier3 = max(0, amount_cents - 50000)
    fee1 = tier1 * 20 // 1000
    fee2 = tier2 * 10 // 1000
    fee3 = tier3 * 5 // 1000
    return fee1 + fee2 + fee3
