#!/usr/bin/env python3
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

elapsed = time.time() - start_time
print(f"Processed {count} results in {elapsed:.2f} seconds")
print(f"Speed: {count/elapsed:.1f} results/second")

