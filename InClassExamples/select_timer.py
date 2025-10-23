from select import select
import datetime
timeout = 2.5

while True:
  try:
    select([], [], [], timeout)
    print(f"Timestamp is: {datetime.datetime.now().timestamp()}")
  except KeyboardInterrupt:
    break