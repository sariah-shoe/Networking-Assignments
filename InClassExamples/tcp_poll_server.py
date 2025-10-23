#!/opt/local/bin/python3.7
import sys
from socket import socket, SOCK_STREAM, AF_INET
from select import poll, POLLIN, POLLOUT, POLLHUP, POLLERR
import traceback

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
    traceback.print_exc()

def recv_data(tcp_sock):
  try:
    data = tcp_sock.recv(4096)
    # Indicates client has disconnected
    if len(data) == 0:
      return False
    print("Received %d bytes" % (len(data)))
    print(data.decode('utf-8'))
    # Echo the data back to the client
    tcp_sock.send(data)
    return True
  except BlockingIOError as b:
    print("Recv failed due to non-blocking IO, this means the client has disconnected?")
    return False
  except Exception as e:
    print_error(e, "recv")
    return False

def main():
  if len(sys.argv) == 3:
    ip = sys.argv[1]
    try:
      port = int(sys.argv[2])
    except:
      print("Port %s unable to be converted to number, run with HOST PORT" % (sys.argv[2]))
      sys.exit(1)
  else:
    print("Run with %s HOST PORT" % (sys.argv[0]))
    sys.exit(1)

  try:
    server_sock = socket(AF_INET, SOCK_STREAM)
  except Exception as e:
    print_error(e, "socket")
    sys.exit(1)
  
  try:
    server_sock.bind((ip, port))
  except Exception as e:
    print_error(e, "bind")
    sys.exit(1)

  try:
    server_sock.listen(10)
  except Exception as e:
    print_error(e, "listen")
    sys.exit(1)

  poller = poll()
  # register server sock for read events
  poller.register(server_sock, POLLIN)
  # register stdin for read events too
  poller.register(sys.stdin, POLLIN)
  quit = False
  client_sockets = []

  while (quit == False):
    try:
      poll_ready_fds = poller.poll(2 * 1000) # 2000ms or 2 seconds
      print(f"poll returned {len(poll_ready_fds)} ready fds")
      if len(poll_ready_fds) > 0:
        print(poll_ready_fds)
    except KeyboardInterrupt as k:
      quit = True
    except Exception as e:
      print_error(e, "poll")

    if check_poll_results(poll_ready_fds, server_sock, POLLIN): # indicates new client has connected
      try:
        client_sock, (client_ip, client_port) = server_sock.accept()
        client_sock.setblocking(0)
        poller.register(client_sock, POLLIN)
        client_sockets.append(client_sock)
        print(client_sock)
        continue
      except KeyboardInterrupt as k:
        quit = True
      except Exception as e:
        print_error(e, "accept")

    for client in client_sockets:
      if check_poll_results(poll_ready_fds, client, POLLIN): # Means client has sent us data
        try:
          ret = recv_data(client)
          if ret == False:
            print("Closing client socket.")
            poller.unregister(client)
            client.close()
            client_sockets.remove(client)
        except KeyboardInterrupt as k:
          quit = True
        except Exception as e:
          print_error(e, "recv_data")

    if check_poll_results(poll_ready_fds, sys.stdin, POLLIN):
      data = sys.stdin.readline().strip()
      print(f"Read {data} from stdin")

  try:
    print("Closing sockets.")
    server_sock.close()
    for client_sock in client_sockets:
      client_sock.close()
  except:
    pass


if __name__ == "__main__":
  main()
