def encode_message(game_id, message_id, flags, game_state, message):
    # mask to widths just in case
    game_id    &= 0xFFFFFF   # 24 bits
    message_id &= 0xFF       # 8 bits
    flags      &= 0x3FFF     # 14 bits
    game_state &= 0x3FFFF    # 18 bits

    header = (
        (game_id << 40) |
        (message_id << 32) |
        (flags << 18) |
        game_state
    )

    header_bytes = header.to_bytes(8, byteorder='big')
    msg_bytes = message.encode('utf-8')
    return header_bytes + msg_bytes

    
def decode_message(message):
    header_bytes = message[:8]
    text_bytes = message[8:]
    header_int = int.from_bytes(header_bytes, "big")
    
    game_id    = (header_int >> 40) & 0xFFFFFF   # 24 bits
    message_id = (header_int >> 32) & 0xFF       # 8 bits
    flags      = (header_int >> 18) & 0x3FFF     # 14 bits
    game_state = header_int & 0x3FFFF    # 18 bits
    
    text = text_bytes.decode("utf-8")
    
    return game_id, message_id, flags, game_state, text

def encode_game_state(game_state):
    encoded = 0
    for row in game_state:
        for cell in row:
            encoded = (encoded << 2) | (cell & 0b11)
    return encoded

def decode_game_state(game_bits):
    decoded = [[0, 0, 0],[0, 0, 0],[0, 0, 0]]
    for row in range(2, -1, -1):
        for col in range(2, -1, -1):
            decoded[row][col] = game_bits & 0b11
            game_bits >>= 2
    return decoded

    