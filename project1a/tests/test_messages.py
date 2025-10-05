from messaging import *
from random import randint

class TestMessages:
    def test_encode_decode(self):
        game_id = randint(0, 0xFFFFFF)
        message_id = randint(0, 0xFF)
        flags = randint(0, 0xFF)
        state = randint(0, 0x3FFFF)
        data = encode_message(game_id, message_id, flags, state, "User Name")

        decoded_game_id, decoded_message_id, decoded_flags, decoded_state, decoded_message = decode_message(data)
        assert game_id == decoded_game_id
        assert message_id == decoded_message_id
        assert flags == decoded_flags
        assert state == decoded_state
        assert "User Name" == decoded_message

    def test_message_one(self):
        message_one_data = encode_message(*MESSAGE_ONE_FIELDS)

        assert message_one_data == MESSAGE_ONE_DATA

        message_one_fields = decode_message(MESSAGE_ONE_DATA)

        assert message_one_fields == MESSAGE_ONE_FIELDS

    def test_message_two(self):
        message_two_data = encode_message(*MESSAGE_TWO_FIELDS)

        assert message_two_data == MESSAGE_TWO_DATA

        message_two_fields = decode_message(MESSAGE_TWO_DATA)

        assert message_two_fields == MESSAGE_TWO_FIELDS

    def test_message_three(self):
        message_three_data = encode_message(*MESSAGE_THREE_FIELDS)

        assert message_three_data == MESSAGE_THREE_DATA

        message_three_fields = decode_message(MESSAGE_THREE_DATA)

        assert message_three_fields == MESSAGE_THREE_FIELDS

    def test_message_four(self):
        message_four_data = encode_message(*MESSAGE_FOUR_FIELDS)

        assert message_four_data == MESSAGE_FOUR_DATA

        message_four_fields = decode_message(MESSAGE_FOUR_DATA)

        assert message_four_fields == MESSAGE_FOUR_FIELDS


MESSAGE_ONE_DATA = 0b1110100010010010010100000000000000000000000000000000000000000000010100000110110001100001011110010110010101110010010101110110111101101110.to_bytes(17, byteorder='big')
MESSAGE_ONE_FIELDS = (15241808, 0, 0, 0, 'PlayerWon')
MESSAGE_TWO_DATA = 0b1110100010010010010100000111011100000000000000100000010000000000.to_bytes(8, byteorder='big')
MESSAGE_TWO_FIELDS = (15241808, 119, 0, 0b100000010000000000, '')
MESSAGE_THREE_DATA = 0b1110100010010010010100000111100100000000000000100000011000000100.to_bytes(8, byteorder='big')
MESSAGE_THREE_FIELDS = (15241808, 121, 0, 0b100000011000000100, '')
MESSAGE_FOUR_DATA = 0b1110100010010010010100000111101100000000000000100001011000000110.to_bytes(8, byteorder='big')
MESSAGE_FOUR_FIELDS = (15241808, 123, 0, 0b100001011000000110, '')