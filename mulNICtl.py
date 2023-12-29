from tap import Connector
from util.trans_graph import LINK_NAME_TO_TX_NAME
import util.ctl as ctl
from tools.read_graph import construct_graph
from util import stream

def write_remote_stream(_stream:stream, sender:str, manifest_name:str):
    cmd = stream.create_command(_stream, f'../stream-replay/data/{manifest_name}.json', clear=True)
    conn = Connector()
    conn.batch(sender, 'abuse_manifest', {'cmd': cmd})
    conn.executor.wait(0.1).apply()

# Graph
topo = construct_graph("./config/topo/lo.txt")


# IP extractor
ip_table = ctl._ip_extract_all(topo)
ctl._ip_associate(topo, ip_table)

# Create Stream
temp = stream.stream()
temp.calc_rtt = True
temp.tx_ipaddrs = ["127.0.0.1"]; temp.tx_parts = [1]; temp.port = 6203
links = topo.get_links()

topo.ADD_STREAM(links[0], temp, target_rtt=18)

print(topo)
ctl.write_remote_stream(topo)

conn = ctl._start_replay(graph=topo, DURATION=1)

print(conn.fetch().apply())

print(ctl.rtt_read(topo))

