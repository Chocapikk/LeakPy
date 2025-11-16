from leakpy import LeakIX
import time

client = LeakIX()

start_time = time.time()
count = 0

events = client.search(scope="leak", query="country:France", use_bulk=True)

for event in events:
    count += 1
    if event.ip and event.port:
        print(f"{count}. {event.protocol}://{event.ip}:{event.port}")
    if count >= 2000:
        break

# HTTP connection is automatically closed when generator is garbage collected
# For immediate closure, you can explicitly call: events.close()

elapsed = time.time() - start_time
print(f"Processed {count} results in {elapsed:.2f} seconds")
print(f"Speed: {count/elapsed:.1f} results/second")

# Example output:
# 1. https://192.168.1.1:443
# 2. http://10.0.0.1:80
# 3. https://172.16.0.1:443
# ...
# Processed 2000 results in 5.29 seconds
# Speed: 378.4 results/second
