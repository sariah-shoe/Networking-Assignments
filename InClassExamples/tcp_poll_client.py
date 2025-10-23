#!/opt/local/bin/python3.7

import sys
from socket import socket, SOCK_STREAM, AF_INET
from select import poll, POLLIN, POLLOUT, POLLERR, POLLHUP


def check_poll_results(ready, socket, event):
  for ready_socket, ready_event in ready:
    if (ready_event & POLLIN) == POLLIN:
      print("POLLIN EVENT")
    if (ready_event & POLLOUT) == POLLOUT:
      print("POLLOUT EVENT")
    if (ready_event & POLLERR) == POLLERR:
      print("POLLERR EVENT")
    if (ready_event & POLLHUP) == POLLHUP:
      print("POLLHUP EVENT")
    if ready_socket == socket.fileno() and (ready_event & event) == event:
      return True
  return False


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
    print(data.decode('utf-8'))
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

  # Create poll object
  poller = poll()

  # Attempt to connect to server
  try:
    tcp_sock.connect((ip, port))
  except Exception as e:
    print_error(e, "connect")

  # We're using select, so set socket to non-blocking just in case
  tcp_sock.setblocking(0)
  # Add client (tcp_sock) and stdin to list of read FDs
  poller.register(tcp_sock, POLLIN)
  poller.register(sys.stdin, POLLIN)

  data_to_send = None
  try:
    while data != 'quit':
      poller.register(tcp_sock, POLLIN)
      write_sockets = []
      if data_to_send != None: # only check if we have data to actually send!
        poller.register(tcp_sock, POLLOUT)

      poll_ready_fds = poller.poll(1 * 1000)
      #print(f"poll returned {len(poll_ready_fds)} sockets!")
      try:
        if check_poll_results(poll_ready_fds, tcp_sock, POLLIN):
          print("poll returned tcp_sock for reading")
          if recv_data(tcp_sock) == False:
            print("Server went away, shutting down.")
            data = 'quit'

        if check_poll_results(poll_ready_fds, tcp_sock, POLLERR):
          print("Server went away, shutting down.")
          data = 'quit'

        if data_to_send != None and check_poll_results(poll_ready_fds, tcp_sock, POLLOUT):
          print("poll returned tcp_sock for writing")
          # now we are _sure_ it's okay to send the data
          send_data(tcp_sock, data_to_send)
          data_to_send = None
          # Have to unregister and re-register so we don't end up in an infinite loop of POLLOUT
          poller.unregister(tcp_sock)
          poller.register(tcp_sock, POLLIN)

        if check_poll_results(poll_ready_fds, sys.stdin, POLLIN):
          print("poll returned stdin")
          data = sys.stdin.readline().strip()
          if data != 'quit':
            data_to_send = data
            # Don't send now, we're not 100% sure we are allowed to
            #send_data(tcp_sock, data)
          else:
            print("Got client quit.")
      except KeyboardInterrupt as e:
        data = 'quit'
        print("Got keyboard kill")

  except Exception as e:
    print_error(e, "send_data")

  finally:
    tcp_sock.close()

if __name__ == "__main__":
  main()
