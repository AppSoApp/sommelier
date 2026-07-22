def apply_percentage_discount_cents(price_cents, percent_off):
    numerator = price_cents * percent_off
    discount = (numerator + 50) // 100
    return price_cents - discount
