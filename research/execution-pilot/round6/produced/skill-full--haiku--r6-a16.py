def apply_percentage_discount_cents(price_cents, percent_off):
    discount = (price_cents * percent_off + 50) // 100
    return price_cents - discount
