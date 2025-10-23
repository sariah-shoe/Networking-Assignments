import sys
from socket import socket, SOCK_STREAM, AF_INET


def print_error(e, f="UNKNOWN"):
    print("Error in %s!" % (f))
    print(e)
    print(type(e))


def recv_data(tcp_sock):
  try:
    data = tcp_sock.recv(100)
    print("Received %d bytes" % (len(data)))
    print(data.decode('utf-8'))
  except Exception as e:
    print_error(e, "recv")


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
    tcp_sock = socket(AF_INET, SOCK_STREAM)
  except Exception as e:
    print_error(e, "socket")
  
  try:
    tcp_sock.bind((ip, port))
  except Exception as e:
    print_error(e, "bind")

  try:
    tcp_sock.listen(10)
  except Exception as e:
    print_error(e, "listen")

  try:
    client_sock, (ip, port) = tcp_sock.accept()
  except Exception as e:
    print_error(e, "accept")
  
  try:
    recv_data(client_sock)
  except Exception as e:
    print_error(e, "recv_data")

  try:
    tcp_sock.close()
    client_sock.close()
  except:
    pass
if __name__ == "__main__":
  main()
