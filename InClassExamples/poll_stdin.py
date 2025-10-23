from select import poll, POLLIN, POLLOUT
import datetime
import sys

def check_poll_results(ready, socket, event):
  for ready_socket, ready_event in ready:
    if ready_socket == socket.fileno() and ready_event == event:
      return True
  return False

timeout = 2 # timeout, float number of seconds


poller = poll()
poller.register(sys.stdin, POLLIN)
while True:
  try:
    ready_fds = poller.poll(timeout * 1000)

    print(f"{len(ready_fds)} fds returned by poll")
    print(ready_fds)
    if len(ready_fds) > 0 and check_poll_results(ready_fds, sys.stdin, POLLIN):
      data = sys.stdin.readline().strip()
      print(f"read data {data} from stdin")
    else:
      print(f"Timestamp is: {datetime.datetime.now().timestamp()}")
  except KeyboardInterrupt:
    break