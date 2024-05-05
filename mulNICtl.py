from tap import Connector
from util.trans_graph import LINK_NAME_TO_TX_NAME
import util.ctl as ctl
from tools.read_graph import construct_graph
from util.solver import channelBalanceSolver
from util import stream
from typing import List
import time, random
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

def throttle_control(fileStreams: List[stream.stream], throttle: int):
    _throttle = int(throttle / len(fileStreams))
    for _ in fileStreams:
        _.throttle = _throttle
    return fileStreams

# Graph
# topo = construct_graph("./config/topo/graph.txt")
topo = construct_graph("./config/topo/graph_4.txt")

# IP extractor
ip_table = ctl._ip_extract_all(topo)
print(ip_table)
ctl._ip_associate(topo, ip_table)

# Create Stream
links = topo.get_links()

temp = stream.stream().read_from_manifest('./config/stream/proj.json')
temp.npy_file = 'proj_12.5MB.npy'
temp.calc_rtt = True
temp.tx_ipaddrs = ['192.168.3.61', '192.168.3.18']; temp.tx_parts = [0.25, 0.25]; temp.port = 6203
topo.ADD_STREAM(links[0], temp, target_rtt=18)


fileStream = stream.stream().read_from_manifest('./config/stream/file.json')
fileStream.tx_ipaddrs = ['192.168.3.61']; fileStream.tx_parts = [0,0]; fileStream.port = 6207
fileStream.throttle = 400
# fileStreams.append(fileStream)
topo.ADD_STREAM(links[0], fileStream)


# fileStream = stream.stream().read_from_manifest('./config/stream/proj.json')
# fileStream.tx_ipaddrs = ['192.168.3.19', '192.168.3.18']; fileStream.tx_parts = [0,0]; fileStream.port = 6205
# fileStream.calc_rtt = False; fileStream.no_logging = True
# topo.ADD_STREAM(links[0], fileStream)

# fileStream = stream.stream().read_from_manifest('./config/stream/proj.json')
# fileStream.tx_ipaddrs = ['192.168.3.19', '192.168.3.18']; fileStream.tx_parts = [0,0]; fileStream.port = 6206
# fileStream.calc_rtt = False; fileStream.no_logging = True
# topo.ADD_STREAM(links[0], fileStream)


f = create_logger_file('logs/2024-1-24/test2.json')

loopTime = 1

choiceRange = [0, 0.25]
import numpy as np
tx_parts_choice             =   np.linspace(choiceRange[0], choiceRange[1], int(choiceRange[1] / 0.05) + 1)
tx_parts_redundancy_choice  =   np.linspace(choiceRange[0], choiceRange[1], int(choiceRange[1] / 0.05) + 1)

_ = 0
for tx_parts_1 in tx_parts_choice:
    for tx_parts_redundence in tx_parts_redundancy_choice:
        phase1 = channelBalanceSolver()
        phase1.update_tx_parts(temp.tx_parts)
        print(f'loop {phase1.tx_parts} with trial {_}')
        _ += 1
        ctl.write_remote_stream(topo)

        for __ in range(loopTime):
            phase_temp = channelBalanceSolver()
            phase_temp.update_tx_parts(phase1.tx_parts)
            conn = ctl._start_replay(graph=topo, DURATION = 30)
            res = ctl._loop_apply(conn)
            print(res)
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

        # phase1.load_balance()
        # phase1.extend_load_balance()
        phase1.tx_parts = [tx_parts_1, tx_parts_1 + tx_parts_redundence]
        phase1.apply(temp)

        f.write(',\n')
        f.flush()
f.write(']')
f.close()



