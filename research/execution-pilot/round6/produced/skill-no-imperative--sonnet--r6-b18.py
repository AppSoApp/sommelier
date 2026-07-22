def swap_nibbles(byte_val):
    if not (0 <= byte_val <= 255):
        raise ValueError("byte_val must be in [0,255]")
    low = byte_val & 0x0F
    high = (byte_val >> 4) & 0x0F
    return (low << 4) | high
