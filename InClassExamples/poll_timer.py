from select import poll, POLLIN, POLLOUT
import datetime
import sys
timeout = 2 # timeout, float number of seconds

poller = poll()
while True:
  try:
    # poll uses msecs, not seconds!
    ready_fds = poller.poll(timeout * 1000)
    print(f"Timestamp is: {datetime.datetime.now().timestamp()}")
  except KeyboardInterrupt:
    break