#!/opt/local/bin/python3.7

import sys
from socket import socket, SOCK_STREAM, AF_INET
from select import select


def print_error(e, f="UNKNOWN"):
    print("Error in %s!" % (f))
    print(e)
    print(type(e))


def send_data(tcp_sock, data):
  try:
    ret = tcp_sock.send(bytes(data, 'utf-8'))
  except KeyboardInterrupt as k:
    raise KeyboardInterrupt()
  except Exception as e:
    print_error(e, "send")


def recv_data(tcp_sock):
  try:
    data = tcp_sock.recv(4096)
    if len(data) == 0:
      return False
    print("Server said: " + data.decode('utf-8'))
    return True
  except Exception as e:
    print_error(e, "recv")

def main():
  if len(sys.argv) >= 3:
    ip = sys.argv[1]
    try:
      port = int(sys.argv[2])
    except:
      print("Port %s unable to be converted to number, run with HOST PORT" % (sys.argv[2]))
      sys.exit(1)
  data = None

  # Create socket to connect to the server
  try:
    tcp_sock = socket(AF_INET, SOCK_STREAM)
  except Exception as e:
    print_error(e, "socket")

  # Attempt to connect to server
  try:
    tcp_sock.connect((ip, port))
  except Exception as e:
    print_error(e, "connect")

  # We're using select, so set socket to non-blocking just in case
  # In case of chat, we don't want blocking because we don't know if keyboard or server are responding next
  tcp_sock.setblocking(0)
  # Add client (tcp_sock) and stdin to list of read FDs
  read_sockets = [tcp_sock, sys.stdin]
  
  try:
    while data != 'quit\n':
      # The parameters sockets to read from, scokets to write to, sockets notify of an error, and timeout
      # Returns sockets
      readlist, writelist, _ = select(read_sockets, [], [], 1)
      try:
        if tcp_sock in readlist:
          if recv_data(tcp_sock) == False:
            print("Server went away, shutting down.")
            data = 'quit'

        # This works in everything but Windows apparently, will want to use WSL
        # Non blocking
        if sys.stdin in readlist:
          data = sys.stdin.readline()
          if data != 'quit\n':
            send_data(tcp_sock, data)
          else:
            print("Got client quit.")
      except KeyboardInterrupt as e:
        data = 'quit'
        print("Got keyboard kill")

  except Exception as e:
    print_error(e, "send_data")

  finally:
    # Want to close so that we aren't using resources on our side or the server side
    tcp_sock.close()

if __name__ == "__main__":
  main()
