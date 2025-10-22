# UDP Tic-Tac-Toe Server

## Run
python server.py <IP or 0.0.0.0> <PORT>

Example:
python server.py 0.0.0.0 7575

## Protocol
- 24-bit game_id (client-chosen, constant)
- 8-bit message_id (server randomizes initial, increments each message)
- 14-bit flags: Bit0 X-to-move, Bit1 O-to-move, Bit2 X-win, Bit3 O-win, Bit4 Tie, Bit5 Error
- 18-bit game state (9 cells × 2 bits)

## Retries
If the client resends the last message_id, the server re-sends its last packet.

## Purge
Inactive games are removed after 5 minutes of no messages.
