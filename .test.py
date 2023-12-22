## Test the stream class
from util.stream import stream, create_command
test = stream()
test.port = 6202
test.tx_parts = [0.9, 0.1]
cmd = create_command(test, '../stream-replay/data/temp.json', clear=True)
print(cmd)

from tap import Connector

conn = Connector()
conn.batch('STA1', 'abuse_manifest', {'cmd': cmd})
conn.executor.wait(0.1).apply()
