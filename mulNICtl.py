from tap import Connector
from util.trans_graph import LINK_NAME_TO_TX_NAME
import util.ctl as ctl
from tools.read_graph import construct_graph
from util.solver import opStruct
from util import stream
import time
import os

def create_logger_file(filename:str):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
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
print(ip_table)
# exit()
ctl._ip_associate(topo, ip_table)


# print(topo)
# Create Stream
links = topo.get_links()
temp = stream.stream()
temp.calc_rtt = True
temp.tx_ipaddrs = ['192.168.3.81', '192.168.3.18']; temp.tx_parts = [0.5, 0.5]; temp.port = 6203
topo.ADD_STREAM(links[0], temp, target_rtt=18)

# fileStream = stream.stream().read_from_manifest('./config/stream/file.json')
# fileStream.tx_ipaddrs = ['192.168.3.81']; fileStream.tx_parts = [0,0]; fileStream.port = 6205
# fileStream.throttle = 500
# topo.ADD_STREAM(links[0], fileStream)

# fileStream = stream.stream().read_from_manifest('./config/stream/proj.json')
# fileStream.tx_ipaddrs = ['192.168.3.19', '192.168.3.18']; fileStream.tx_parts = [0,0]; fileStream.port = 6205
# fileStream.calc_rtt = False; fileStream.no_logging = True
# topo.ADD_STREAM(links[0], fileStream)

# fileStream = stream.stream().read_from_manifest('./config/stream/proj.json')
# fileStream.tx_ipaddrs = ['192.168.3.19', '192.168.3.18']; fileStream.tx_parts = [0,0]; fileStream.port = 6206
# fileStream.calc_rtt = False; fileStream.no_logging = True
# topo.ADD_STREAM(links[0], fileStream)




f = create_logger_file('logs/2024-1-22/test.json')

loopTime = 1

for _ in range(30):
    phase1 = opStruct()
    phase1.update_tx_parts(temp.tx_parts)
    print(f'loop {phase1.tx_parts} with trial {_}')
    if _ == 15:
        fileStream = stream.stream().read_from_manifest('./config/stream/file.json')
        fileStream.tx_ipaddrs = ['192.168.3.81']; fileStream.tx_parts = [0,0]; fileStream.port = 6204; fileStream.tos = 128
        fileStream.throttle = 400
        topo.ADD_STREAM(links[0], fileStream)
        # print(topo)
        # exit()
    ctl.write_remote_stream(topo)

    for __ in range(loopTime):
        phase_temp = opStruct()
        phase_temp.update_tx_parts(phase1.tx_parts)
        conn = ctl._start_replay(graph=topo, DURATION = 100)
        res = ctl._loop_apply(conn)
        # print(res)
        try:
            ctl.rtt_read(topo, [phase_temp])
        except Exception as e:
            print(e)
            continue
        phase1 = phase1 + phase_temp
        # print("phase1", phase1,"phase_temp", phase_temp)
    phase1 = phase1 / loopTime
    print(phase1)
    f.write(phase1.__str__())


    phase1.load_balance()
    # phase1.extend_load_balance()
    phase1.apply(temp)

    f.write(',\n')
    f.flush()
f.write(']')
f.close()



