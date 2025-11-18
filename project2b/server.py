import sys
import json
import socket
import select
from socket import AF_INET, SOCK_STREAM


MAX_PACKET_BYTES = 4096
MAX_NAME_BYTES = 60
MAX_MESSAGE_BYTES = 3800


class ClientState:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.user_name: str | None = None
        self.rooms: set[str] = set()
        self.recv_buffer = b""
        self.send_buffer = b""


def verify_args():
    if len(sys.argv) != 3:
        sys.exit("The server requires two values to run, the IP Address and Port Number")
    host = sys.argv[1]
    try:
        port = int(sys.argv[2])
    except ValueError:
        sys.exit("Port must be a number")
    return host, port


def print_error(e, where="UNKNOWN"):
    print(f"Error in {where}!")
    print(e)
    print(type(e))


def queue_json(client: ClientState, obj: dict, write_sockets: list[socket.socket]):
    """Encode JSON, append newline, and queue for sending."""
    try:
        encoded = json.dumps(obj, separators=(",", ":")).encode("utf-8") + b"\n"
    except Exception as e:
        print_error(e, "queue_json json.dumps")
        return
    
    client.send_buffer += encoded
    if client.sock not in write_sockets:
        write_sockets.append(client.sock)


def queue_chat(client: ClientState, msg: dict, write_sockets: list[socket.socket]):
    packet = {"status": "chat", "history": [msg]}
    queue_json(client, packet, write_sockets)


def queue_error(client: ClientState, message: str, write_sockets: list[socket.socket]):
    packet = {"status": "error", "message": message}
    queue_json(client, packet, write_sockets)


def queue_disconnect(client: ClientState, write_sockets: list[socket.socket]):
    packet = {"status": "disconnect"}
    queue_json(client, packet, write_sockets)


def validate_name(field_value: str, expect_prefix: str | None) -> bool:
    if not isinstance(field_value, str):
        return False
    try:
        data = field_value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    if len(data) > MAX_NAME_BYTES:
        return False
    if expect_prefix is not None and not field_value.startswith(expect_prefix):
        return False
    return True


def validate_message_field(text: str) -> bool:
    if not isinstance(text, str):
        return False
    try:
        data = text.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return len(data) <= MAX_MESSAGE_BYTES


def handle_connect(pkt: dict, client: ClientState,
                   clients_by_name: dict[str, ClientState],
                   rooms_subscribers: dict[str, set[ClientState]],
                   write_sockets: list[socket.socket]):
    # Required fields: user_name, targets (list)
    if "user_name" not in pkt or "targets" not in pkt:
        queue_error(client, "Missing Required Field", write_sockets)
        return

    user_name = pkt["user_name"]
    targets = pkt["targets"]

    if not validate_name(user_name, "@"):
        queue_error(client, "Fields Longer Than Limits", write_sockets)
        return

    if not isinstance(targets, list):
        queue_error(client, "Missing Required Field", write_sockets)
        return

    # Ensure unique user name
    if user_name in clients_by_name and clients_by_name[user_name] is not client:
        queue_error(client, "User name already connected", write_sockets)
        return

    # Register client
    client.user_name = user_name
    clients_by_name[user_name] = client

    # Register room subscriptions
    client.rooms.clear()
    for t in targets:
        if not isinstance(t, str):
            continue
        if not validate_name(t, "#"):
            queue_error(client, "Fields Longer Than Limits", write_sockets)
            return
        client.rooms.add(t)
        rooms_subscribers.setdefault(t, set()).add(client)


def handle_message(pkt: dict, client: ClientState,
                   clients_by_name: dict[str, ClientState],
                   rooms_subscribers: dict[str, set[ClientState]],
                   write_sockets: list[socket.socket]):
    # Client must have connected first
    if client.user_name is None:
        queue_error(client, "Client not connected", write_sockets)
        return

    # Required fields: user_name, target, message
    if "user_name" not in pkt or "target" not in pkt or "message" not in pkt:
        queue_error(client, "Missing Required Field", write_sockets)
        return

    # The user_name field in the packet should match the connected user
    user_name = pkt["user_name"]
    if user_name != client.user_name:
        queue_error(client, "User name mismatch", write_sockets)
        return

    target = pkt["target"]
    message_text = pkt["message"]

    # Validate fields
    prefix = "#" if isinstance(target, str) and target.startswith("#") else "@"
    if not validate_name(target, prefix):
        queue_error(client, "Fields Longer Than Limits", write_sockets)
        return

    if not validate_message_field(message_text):
        queue_error(client, "Fields Longer Than Limits", write_sockets)
        return

    msg = {
        "target": target,
        "from": client.user_name,
        "message": message_text,
    }

    # Room message
    if target.startswith("#"):
        # Auto-subscribe sender if they aren't already in the room
        if target not in client.rooms:
            client.rooms.add(target)
            rooms_subscribers.setdefault(target, set()).add(client)

        subscribers = rooms_subscribers.get(target, set())
        for dest in subscribers:
            if dest is client:
                continue
            queue_chat(dest, msg, write_sockets)

    # Direct message
    elif target.startswith("@"):
        dest = clients_by_name.get(target)
        if dest is None:
            queue_error(client, "Target user not connected", write_sockets)
            return
        queue_chat(dest, msg, write_sockets)

def disconnect_client(client: ClientState,
                      read_sockets: list[socket.socket],
                      write_sockets: list[socket.socket],
                      except_sockets: list[socket.socket],
                      clients_by_sock: dict[socket.socket, ClientState],
                      clients_by_name: dict[str, ClientState],
                      rooms_subscribers: dict[str, set[ClientState]]):
    sock = client.sock
    # Remove from name map
    if client.user_name is not None:
        if clients_by_name.get(client.user_name) is client:
            del clients_by_name[client.user_name]
    # Remove from rooms
    for room in list(client.rooms):
        subs = rooms_subscribers.get(room)
        if subs is not None and client in subs:
            subs.remove(client)
        if subs is not None and not subs:
            del rooms_subscribers[room]

    # Remove from socket lists
    for lst in (read_sockets, write_sockets, except_sockets):
        if sock in lst:
            lst.remove(sock)

    # Remove from main mapping
    clients_by_sock.pop(sock, None)

    # Close socket
    try:
        sock.close()
    except Exception:
        pass


def process_packet_line(line: str, client: ClientState,
                        read_sockets: list[socket.socket],
                        write_sockets: list[socket.socket],
                        except_sockets: list[socket.socket],
                        clients_by_sock: dict[socket.socket, ClientState],
                        clients_by_name: dict[str, ClientState],
                        rooms_subscribers: dict[str, set[ClientState]]):
    # Enforce packet size
    if len(line.encode("utf-8")) > MAX_PACKET_BYTES:
        queue_error(client, "Message Longer Than 4096 Bytes", write_sockets)
        return

    try:
        pkt = json.loads(line)
    except Exception:
        queue_error(client, "Malformed JSON", write_sockets)
        return

    if not isinstance(pkt, dict):
        queue_error(client, "Malformed JSON", write_sockets)
        return

    action = pkt.get("action")
    if action is None:
        queue_error(client, "Missing Required Field", write_sockets)
        return

    if action == "connect":
        handle_connect(pkt, client, clients_by_name, rooms_subscribers, write_sockets)
    elif action == "message":
        handle_message(pkt, client, clients_by_name, rooms_subscribers, write_sockets)
    elif action == "disconnect":
        # Client is disconnecting; clean up.
        disconnect_client(client, read_sockets, write_sockets, except_sockets,
                          clients_by_sock, clients_by_name, rooms_subscribers)
    else:
        queue_error(client, f"{action} is not a valid action", write_sockets)


def handle_client_read(client: ClientState,
                       read_sockets: list[socket.socket],
                       write_sockets: list[socket.socket],
                       except_sockets: list[socket.socket],
                       clients_by_sock: dict[socket.socket, ClientState],
                       clients_by_name: dict[str, ClientState],
                       rooms_subscribers: dict[str, set[ClientState]]):
    sock = client.sock
    try:
        data = sock.recv(65536)
    except BlockingIOError:
        return
    except ConnectionResetError:
        # Treat as clean disconnect
        disconnect_client(client, read_sockets, write_sockets, except_sockets,
                          clients_by_sock, clients_by_name, rooms_subscribers)
        return
    except Exception as e:
        print_error(e, "recv")
        disconnect_client(client, read_sockets, write_sockets, except_sockets,
                          clients_by_sock, clients_by_name, rooms_subscribers)
        return

    if not data:
        # Remote closed
        disconnect_client(client, read_sockets, write_sockets, except_sockets,
                          clients_by_sock, clients_by_name, rooms_subscribers)
        return

    # Decode UTF-8 strictly
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        queue_error(client, "Malformed UTF-8 Data", write_sockets)
        return

    # Process line-delimited JSON
    for line in filter(None, text.splitlines()):
        process_packet_line(line, client,
                            read_sockets, write_sockets, except_sockets,
                            clients_by_sock, clients_by_name, rooms_subscribers)


def handle_client_write(client: ClientState,
                        read_sockets: list[socket.socket],
                        write_sockets: list[socket.socket],
                        except_sockets: list[socket.socket],
                        clients_by_sock: dict[socket.socket, ClientState],
                        clients_by_name: dict[str, ClientState],
                        rooms_subscribers: dict[str, set[ClientState]]):
    if not client.send_buffer:
        # Nothing to send
        if client.sock in write_sockets:
            write_sockets.remove(client.sock)
        return

    try:
        sent = client.sock.send(client.send_buffer)
    except BlockingIOError:
        return
    except ConnectionResetError:
        disconnect_client(client, read_sockets, write_sockets, except_sockets,
                          clients_by_sock, clients_by_name, rooms_subscribers)
        return
    except Exception as e:
        print_error(e, "send")
        disconnect_client(client, read_sockets, write_sockets, except_sockets,
                          clients_by_sock, clients_by_name, rooms_subscribers)
        return

    client.send_buffer = client.send_buffer[sent:]
    if not client.send_buffer and client.sock in write_sockets:
        write_sockets.remove(client.sock)


def main():
    host, port = verify_args()

    try:
        server_sock = socket.socket(AF_INET, SOCK_STREAM)
    except Exception as e:
        print_error(e, "socket")
        sys.exit(1)

    try:
        server_sock.bind((host, port))
    except Exception as e:
        print_error(e, "bind")
        sys.exit(1)

    try:
        server_sock.listen(10)
    except Exception as e:
        print_error(e, "listen")
        sys.exit(1)

    server_sock.setblocking(False)

    read_sockets: list[socket.socket] = [server_sock]
    write_sockets: list[socket.socket] = []
    except_sockets: list[socket.socket] = [server_sock]

    clients_by_sock: dict[socket.socket, ClientState] = {}
    clients_by_name: dict[str, ClientState] = {}
    rooms_subscribers: dict[str, set[ClientState]] = {}

    try:
        while True:
            try:
                rlist, wlist, xlist = select.select(read_sockets, write_sockets, except_sockets)
            except KeyboardInterrupt:
                # Graceful shutdown: tell all clients we're disconnecting.
                for c in list(clients_by_sock.values()):
                    queue_disconnect(c, write_sockets)
                # Best-effort flush
                for c in list(clients_by_sock.values()):
                    if c.send_buffer:
                        try:
                            c.sock.sendall(c.send_buffer)
                        except Exception:
                            pass
                    try:
                        c.sock.close()
                    except Exception:
                        pass
                try:
                    server_sock.close()
                except Exception:
                    pass
                break
            except Exception as e:
                print_error(e, "select")
                continue

            # Handle new connections and reads
            for sock in rlist:
                if sock is server_sock:
                    # Accept a new client
                    try:
                        client_sock, addr = server_sock.accept()
                        client_sock.setblocking(False)
                    except Exception as e:
                        print_error(e, "accept")
                        continue

                    cs = ClientState(client_sock)
                    clients_by_sock[client_sock] = cs
                    read_sockets.append(client_sock)
                    except_sockets.append(client_sock)
                else:
                    client = clients_by_sock.get(sock)
                    if client is not None:
                        handle_client_read(client,
                                           read_sockets, write_sockets, except_sockets,
                                           clients_by_sock, clients_by_name, rooms_subscribers)

            # Handle writes
            for sock in list(wlist):
                client = clients_by_sock.get(sock)
                if client is not None:
                    handle_client_write(client,
                                        read_sockets, write_sockets, except_sockets,
                                        clients_by_sock, clients_by_name, rooms_subscribers)

            # Handle exceptions
            for sock in xlist:
                if sock is server_sock:
                    # Fatal error on listening socket; shut down.
                    print("Fatal error on server socket; shutting down.")
                    for c in list(clients_by_sock.values()):
                        queue_disconnect(c, write_sockets)
                        try:
                            if c.send_buffer:
                                c.sock.sendall(c.send_buffer)
                        except Exception:
                            pass
                        try:
                            c.sock.close()
                        except Exception:
                            pass
                    try:
                        server_sock.close()
                    except Exception:
                        pass
                    return
                else:
                    client = clients_by_sock.get(sock)
                    if client is not None:
                        disconnect_client(client,
                                          read_sockets, write_sockets, except_sockets,
                                          clients_by_sock, clients_by_name, rooms_subscribers)
    finally:
        try:
            server_sock.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
