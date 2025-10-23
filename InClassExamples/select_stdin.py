from select import select
import datetime
import sys
timeout = 2.5 # timeout, float number of seconds
read_sockets = []
write_sockets = []
exception_sockets = []
read_sockets.append(sys.stdin)
while True:
  try:
    read_ready, _, _ = select(read_sockets, write_sockets, exception_sockets, timeout)
    if sys.stdin in read_ready:
      user_data = sys.stdin.readline()
      print(f"Read `{user_data.strip()}' from user")
    else:
      print(f"No new input at {datetime.datetime.now().timestamp()}")
  except KeyboardInterrupt:
    break