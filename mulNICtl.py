from tap import Connector
from util.trans_graph import LINK_NAME_TO_TX_NAME
import util.ctl as ctl
from tools.read_graph import construct_graph
from util.solver import opStruct
from util import stream
import time
import os

def create_logger_file(filename:str):
    f = open(filename, 'w')
    f.write('[')
    return f


def write_remote_stream(_stream:stream, sender:str, manifest_name:str):
    cmd = stream.create_command(_stream, f'../stream-replay/data/{manifest_name}.json', clear=True)
    conn = Connector()
    conn.batch(sender, 'abuse_manifest', {'cmd': cmd})
    conn.executor.wait(0.1).apply()

# Graph
topo = construct_graph("./config/topo/graph.txt")


# IP extractor
ip_table = ctl._ip_extract_all(topo)
ctl._ip_associate(topo, ip_table)


# print(topo)
# Create Stream
links = topo.get_links()
temp = stream.stream()
temp.calc_rtt = True
temp.tx_ipaddrs = ['192.168.3.64', '192.168.3.18']; temp.tx_parts = [0.05, 0.05]; temp.port = 6203
topo.ADD_STREAM(links[0], temp, target_rtt=18)

fileStream = stream.stream().read_from_manifest('./config/stream/file.json')
fileStream.tx_ipaddrs = ['192.168.3.64']; fileStream.tx_parts = [0,0]; fileStream.port = 6204
fileStream.throttle = 100
topo.ADD_STREAM(links[0], fileStream)

# fileStream = stream.stream().read_from_manifest('./config/stream/proj.json')
# fileStream.tx_ipaddrs = ['192.168.3.19', '192.168.3.18']; fileStream.tx_parts = [0,0]; fileStream.port = 6205
# fileStream.calc_rtt = False; fileStream.no_logging = True
# topo.ADD_STREAM(links[0], fileStream)

# fileStream = stream.stream().read_from_manifest('./config/stream/proj.json')
# fileStream.tx_ipaddrs = ['192.168.3.19', '192.168.3.18']; fileStream.tx_parts = [0,0]; fileStream.port = 6206
# fileStream.calc_rtt = False; fileStream.no_logging = True
# topo.ADD_STREAM(links[0], fileStream)


phase1 = opStruct()
phase1.update_tx_parts(temp.tx_parts)

f = create_logger_file('logs/pha1_0.7_0.7.json')
# print(topo)
# while True:
for _ in range(30):
    print(f'loop {phase1.tx_parts}')
    ctl.write_remote_stream(topo)
    # conn = Connector()
    # conn.batch('STA1', 'config_network', {'interface': "wlx081f7163a93d wlx081f7163a94f wlx081f7163a912"}).wait(0.1).apply()
    conn = ctl._start_replay(graph=topo, DURATION = 150)

    res = ctl._loop_apply(conn)
    print(res)
    try:
        ctl.rtt_read(topo, [phase1])
    except Exception as e:
        print(e)
        continue
    print(phase1)
    f.write(phase1.__str__())


    phase1.load_balance()
    # phase1.extend_load_balance()
    phase1.apply(temp)

    # if phase1.check_load_balance():
    #     # break
    #     counter = 1
    # else:
    f.write(',\n')
    f.flush()


f.write(']')
f.close()



