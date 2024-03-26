import subprocess as sp

SHELL_POPEN = lambda x: sp.Popen(x, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
SHELL_RUN = lambda x: sp.run(x, stdout=sp.PIPE, stderr=sp.PIPE, check=True, shell=True)
## Test the stream class
def test_steam_gen():
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

def test_channel_throughput():
    from tap import Connector
    from util.trans_graph import LINK_NAME_TO_TX_NAME
    import util.ctl as ctl
    from tools.read_graph import construct_graph
    from util.solver import opStruct
    from util import stream
    from typing import List
    import time, random
    import os

    print("Test Channel 0")
    # Graph
    # topo = construct_graph("./config/topo/graph.txt")
    topo = construct_graph("./config/topo/graph_4.txt")
    links = topo.get_links()

    # IP extractor
    ip_table = ctl._ip_extract_all(topo)
    ctl._ip_associate(topo, ip_table)

    ip_ch1 = "192.168.3.57"
    ip_ch2 = "192.168.3.59"
    # assert ip_ch1 in ip_table and ip_ch2 in ip_table

    temp = stream.stream().read_from_manifest('./config/stream/file.json')
    temp.tx_ipaddrs = ['192.168.3.57', '192.168.3.59']; temp.tx_parts = [0, 0]; temp.port = 6230
    temp.calc_rtt = False; temp.no_logging = True
    topo.ADD_STREAM(links[0], temp, target_rtt=16)

    ctl.write_remote_stream(topo)
    conn = ctl._start_replay(graph=topo, DURATION = 30)
    res = ctl._loop_apply(conn)
    print(res)


    print("Test Channel 1")
    topo = construct_graph("./config/topo/graph_4.txt")
    links = topo.get_links()

    ip_table = ctl._ip_extract_all(topo)
    ctl._ip_associate(topo, ip_table)

    temp = stream.stream().read_from_manifest('./config/stream/file.json')

    temp.tx_ipaddrs = ['192.168.3.57', '192.168.3.59']; temp.tx_parts = [1, 1]; temp.port = 6203
    topo.ADD_STREAM(links[0], temp, target_rtt=16)
    temp.calc_rtt = False; temp.no_logging = True

    ctl.write_remote_stream(topo)
    conn = ctl._start_replay(graph=topo, DURATION = 30)
    res = ctl._loop_apply(conn)
    print(res)

def test_local_throughput():
    import time
    process = []
    process.append(SHELL_POPEN('python3 tap.py -s'))
    time.sleep(1)
    process.append(SHELL_POPEN('python3 tap.py -c 127.0.0.1 -n SoftAP'))
    process.append(SHELL_POPEN('python3 tap.py -c 127.0.0.1 -n STA1'))
    time.sleep(2)
        

    from tap import Connector
    from util.trans_graph import LINK_NAME_TO_TX_NAME
    import util.ctl as ctl
    from tools.read_graph import construct_graph
    from util.solver import opStruct
    from util import stream
    from typing import List
    import time, random
    import os

    print("Test Channel 0")
    # Graph
    # topo = construct_graph("./config/topo/graph.txt")
    topo = construct_graph("./config/topo/lo.txt")
    links = topo.get_links()

    # IP extractor
    ip_table = ctl._ip_extract_all(topo)
    ctl._ip_associate(topo, ip_table)

    temp = stream.stream().read_from_manifest('./config/stream/file.json')
    temp.tx_ipaddrs = ['127.0.0.1', '10.16.60.57']; temp.tx_parts = [0, 0]; temp.port = 6203
    temp.calc_rtt = False; temp.no_logging = True
    topo.ADD_STREAM(links[0], temp)

    ctl.write_remote_stream(topo)
    conn = ctl._start_replay(topo, 5)
    res = ctl._loop_apply(conn)
    print(res)


    print("Test Channel 1")
    topo = construct_graph("./config/topo/lo.txt")
    links = topo.get_links()


    ip_table = ctl._ip_extract_all(topo)
    ctl._ip_associate(topo, ip_table)

    temp = stream.stream().read_from_manifest('./config/stream/file.json')

    temp.tx_ipaddrs = ['127.0.0.1', '10.16.60.57']; temp.tx_parts = [1, 1]; temp.port = 6203
    temp.calc_rtt = False; temp.no_logging = True
    topo.ADD_STREAM(links[0], temp, target_rtt=16)

    ctl.write_remote_stream(topo)
    conn = ctl._start_replay(graph=topo, DURATION = 5)
    res = ctl._loop_apply(conn)
    print(res)

    process.append(SHELL_POPEN('killall python3'))
   
def test_proj_transmission():
    from tap import Connector
    from util.trans_graph import LINK_NAME_TO_TX_NAME
    import util.ctl as ctl
    from tools.read_graph import construct_graph
    from util.solver import opStruct
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

    # Graph
    # topo = construct_graph("./config/topo/graph.txt")
    topo = construct_graph("./config/topo/graph_4.txt")


    # IP extractor
    ip_table = ctl._ip_extract_all(topo)
    ctl._ip_associate(topo, ip_table)

    links = topo.get_links()

    temp = stream.stream().read_from_manifest('./config/stream/proj.json')
    # temp.npy_file = 'proj_12.5MB.npy'
    temp.calc_rtt = True
    temp.tx_ipaddrs = ['192.168.3.57', '192.168.3.59']; temp.tx_parts = [0.25, 0.25]; temp.port = 6203
    topo.ADD_STREAM(links[0], temp, target_rtt=16)

    temp_stream2 = stream.stream().read_from_manifest('./config/stream/proj.json')
    temp_stream2.calc_rtt = True
    temp_stream2.tx_ipaddrs = ['192.168.3.57', '192.168.3.59']; temp_stream2.tx_parts = [0.25, 0.25]; temp_stream2.port = 6320
    topo.ADD_STREAM(links[0], temp_stream2, target_rtt=16)

    f = create_logger_file('logs/2024-3-26/test1.json')

    loopTime = 1
    choiceRange = [0, 0.25]
    import numpy as np
    # tx_parts_choice =  np.linspace(choiceRange[0], choiceRange[1], int(choiceRange[1] / 0.05) + 1)
    # tx_parts_redundancy_choice = np.linspace(choiceRange[0], choiceRange[1], int(choiceRange[1] / 0.05) + 1)

    tx_parts_choice =  np.array([0.9, 0.6])
    tx_parts_redundancy_choice = np.array([0] * len(tx_parts_choice))
    for tx_parts_1, tx_parts_redundency in zip(tx_parts_choice, tx_parts_redundancy_choice):
        phase1 = opStruct()
        phase1.update_tx_parts([tx_parts_1, tx_parts_1 + tx_parts_redundency])
        phase1.apply(temp)
        # phase1.update_tx_parts(temp.tx_parts)
        print(f'Test {phase1.tx_parts}')

        ctl.write_remote_stream(topo)

        for __ in range(loopTime):
            phase_temp = opStruct()
            phase_temp.update_tx_parts(phase1.tx_parts)

            conn = ctl._start_replay(graph=topo, DURATION = 30)
            res = ctl._loop_apply(conn)
            print(res)

            try:
                ctl.rtt_read(topo, [phase_temp])
            except Exception as e:
                print(e)
                continue
            
            print(phase_temp.correct_channel_rtt())
            phase1 = phase1 + phase_temp

        phase1 = phase1 / loopTime
        print(phase1)

        # phase1.tx_parts = [tx_parts_1, tx_parts_1 + tx_parts_redundency]


        f.write(phase1.__str__())
        if tx_parts_1 != tx_parts_choice[-1]:
            f.write(',\n')

        f.flush()

    f.write(']')
    f.close()

def test_line_predict():
    from tap import Connector
    from util.trans_graph import LINK_NAME_TO_TX_NAME
    import util.ctl as ctl
    from tools.read_graph import construct_graph
    from util.solver import opStruct
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

    # Graph
    # topo = construct_graph("./config/topo/graph.txt")
    topo = construct_graph("./config/topo/graph_4.txt")


    # IP extractor
    ip_table = ctl._ip_extract_all(topo)
    ctl._ip_associate(topo, ip_table)

    links = topo.get_links()

    temp = stream.stream().read_from_manifest('./config/stream/proj.json')
    # temp.npy_file = 'proj_12.5MB.npy'
    temp.calc_rtt = True
    temp.tx_ipaddrs = ['192.168.3.57', '192.168.3.59']; temp.tx_parts = [0.25, 0.25]; temp.port = 6203
    topo.ADD_STREAM(links[0], temp, target_rtt=16)

    temp_stream2 = stream.stream().read_from_manifest('./config/stream/proj.json')
    temp_stream2.calc_rtt = True
    temp_stream2.tx_ipaddrs = ['192.168.3.57', '192.168.3.59']; temp_stream2.tx_parts = [0.25, 0.25]; temp_stream2.port = 6320
    topo.ADD_STREAM(links[0], temp_stream2, target_rtt=16)

    f = create_logger_file('logs/2024-3-26/test1.json')

    loopTime = 1
    choiceRange = [0, 0.25]
    import numpy as np
    # tx_parts_choice =  np.linspace(choiceRange[0], choiceRange[1], int(choiceRange[1] / 0.05) + 1)
    # tx_parts_redundancy_choice = np.linspace(choiceRange[0], choiceRange[1], int(choiceRange[1] / 0.05) + 1)

    tx_parts_choice =  np.array([0.9, 0.6])
    tx_parts_redundancy_choice = np.array([0] * len(tx_parts_choice))
    phase_list_1 = []
    phase_list_2 = []
    for tx_parts_1, tx_parts_redundency in zip(tx_parts_choice, tx_parts_redundancy_choice):
        phase1 = opStruct(); phase2 = opStruct()
        phase1.update_tx_parts([tx_parts_1, tx_parts_1 + tx_parts_redundency])
        phase2.update_tx_parts([tx_parts_1, tx_parts_1 + tx_parts_redundency])

        phase1.apply(temp)
        # phase1.update_tx_parts(temp.tx_parts)
        print(f'Test {phase1.tx_parts}')

        ctl.write_remote_stream(topo)

        for __ in range(loopTime):
            phase_temp = opStruct()
            phase_temp.update_tx_parts(phase1.tx_parts)

            conn = ctl._start_replay(graph=topo, DURATION = 30)
            res = ctl._loop_apply(conn)
            print(res)

            try:
                ctl.rtt_read(topo, [phase_temp, phase2])
            except Exception as e:
                print(e)
                continue
            
            print(phase_temp.correct_channel_rtt())
            phase1 = phase1 + phase_temp

        phase1 = phase1 / loopTime
        print(phase1)
        print(phase2)
        phase_list_1.append(phase1)
        phase_list_2.append(phase2)
        f.write(phase1.__str__())
        f.write(',\n')
        f.write(phase2.__str__())
        f.write(',\n')

        f.flush()

    from scripts.line_infer import line_infer_func, find_minimum_part
    task1_cha1 = line_infer_func(phase_list_1, 0)
    task2_cha2 = line_infer_func(phase_list_1, 1)

    infered_funcs = [ line_infer_func(phase_list_2, channel) for channel in range(2)] 
    
    minimum_part = find_minimum_part(task1_cha1, task2_cha2)

    # Infer value
    infered_rtt_per_channel_task1 = [task1_cha1(minimum_part), task2_cha2(minimum_part)]
    infered_rtt_per_channel_task2 = [func(minimum_part) for func in infered_funcs]

    # Run the test
    for tx_parts_1, tx_parts_redundency in zip([minimum_part], [0]):
        phase1 = opStruct(); phase2 = opStruct()
        phase1.update_tx_parts([tx_parts_1, tx_parts_1 + tx_parts_redundency])
        phase2.update_tx_parts([tx_parts_1, tx_parts_1 + tx_parts_redundency])

        phase1.apply(temp)
        # phase1.update_tx_parts(temp.tx_parts)
        print(f'Test {phase1.tx_parts}')

        ctl.write_remote_stream(topo)

        for __ in range(loopTime):
            phase_temp = opStruct()
            phase_temp.update_tx_parts(phase1.tx_parts)

            conn = ctl._start_replay(graph=topo, DURATION = 30)
            res = ctl._loop_apply(conn)
            print(res)

            try:
                ctl.rtt_read(topo, [phase_temp, phase2])
            except Exception as e:
                print(e)
                continue
            
            print(phase_temp.correct_channel_rtt())
            phase1 = phase1 + phase_temp

        phase1 = phase1 / loopTime
        print(phase1)
        print(phase2)
        phase_list_1.append(phase1)
        phase_list_2.append(phase2)
        f.write(phase1.__str__())
        f.write(',\n')
        f.write(phase2.__str__())
        f.flush()



    print(infered_rtt_per_channel_task1)
    print(infered_rtt_per_channel_task2)


    f.write(']')
    f.close()

if __name__ == '__main__':
    # test_proj_transmission()
    test_line_predict()
    # test_channel_throughput()
    # test_local_throughput()


