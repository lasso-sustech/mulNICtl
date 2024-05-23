#!/usr/bin/env python3
from tap import Connector

conn = Connector()
clients = conn.list_all()
conns = [Connector(c) for c in clients]
for c in conns:
    conn.batch(c.client, 'warm_up_tx', {})
conn.executor.fetch()
while True:
    try:
        outputs = conn.executor.apply()
        break
    except:
        continue
print(outputs)

conn = Connector()
clients = conn.list_all()
conns = [Connector(c) for c in clients]
for c in conns:
    conn.batch(c.client, 'warm_up_rx', {})
conn.executor.fetch()
while True:
    try:
        outputs = conn.executor.apply()
        break
    except:
        continue
print(outputs)