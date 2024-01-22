import json
import sys
import os
from util.trans_graph import Graph
from util.trans_graph import LINK_NAME_TO_TX_NAME, LINK_NAME_TO_RX_NAME, LINK_NAME_TO_PROT_NAME
from util.solver import dataStruct
from util.stream import stream, create_command
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from tap import Connector

## ip setup component
def _ip_extract_all(graph: Graph):
    """
    Extract ip from controlled device, store ip table into temp/ip_table.json
    """
    conn = Connector()
    ip_table = {}
    for device_name, _ in graph.graph.items():
        conn.batch(device_name, "read_ip_addr")
    outputs = conn.executor.wait(1).fetch().apply()
    results = [o["ip_addr"] for o in outputs]
    for r, c in zip(results, graph.graph.keys()):
        ip_table.update({c: {}})
        try:
            ipv4_addrs = eval(r)
        except:
            print("Error: client %s do not exist valid ipv4 addr" % c)
        else:
            # Generally multiple ipv4 with same name might be detect, but we only need the first one
            for ipv4_addr in ipv4_addrs:
                ip_table[c].update({ipv4_addr[0]: ipv4_addr[1]})

    # save the dict into json file
    with open("./temp/ip_table.json", "w") as f:
        json.dump(ip_table, f)

    return ip_table

def _ip_associate(graph:Graph, ip_table:dict):
    for device_name in ip_table.keys():
        _depart_name = device_name.split("-")
        if len(_depart_name) > 1:
            _, ind = device_name.split("-")
            idx = 0
            for protocol, ip in ip_table[device_name].items():
                graph.info_graph[device_name].update({"ind": int(ind)})
                graph.associate_ip(
                    device_name, protocol, ip
                )  # default take the previous three as indicator to protocol
                idx += 1
        else:
            for protocol, ip in ip_table[device_name].items():
                graph.associate_ip(device_name, protocol, ip)
    return _add_ipc_port(graph)

def _add_ipc_port(graph):
    """
    Add ipc port (remote and local) to graph
    """
    port = 11112
    for device_name in graph.graph.keys():
        for link_name in graph.graph[device_name].keys():
            graph.info_graph[device_name][link_name].update({"ipc_port": port})
            graph.info_graph[device_name][link_name].update(
                {"local_port": port - 1024}
            )
            port += 1
    return graph


def _start_replay(graph:Graph, DURATION):
    """
    Construct a transmission ready connector waiting to be applied
    """
    conn = Connector()
    # start reception
    for device_name, links in graph.graph.items():
        for link_name, streams in links.items():
            # split link name to protocol, sender, receiver
            # prot, sender, receiver = link_name.split("_")
            # receiver = receiver if receiver else ""
            receiver = LINK_NAME_TO_RX_NAME(link_name)
            for stream_name, stream_handle in streams.items():
                # extract port number
                port_num, tos = stream_name.split("@")
                if stream_handle.calc_rtt == False:
                    # continue
                    conn.batch(
                        receiver,
                        "outputs_throughput",
                        {"port": port_num, "duration": DURATION},
                        timeout= DURATION + 5,
                    )
                else:
                    conn.batch(
                        receiver,
                        "outputs_throughput_jitter",
                        {
                            "port": port_num,
                            "duration": DURATION,
                            "calc_rtt": "--calc-rtt",
                            "tos": tos,
                        },
                        timeout=DURATION + 5,
                    )

    conn.executor.wait(1)
    # start transmission
    for device_name, links in graph.graph.items():
        for link_name, streams in links.items():
            if streams == {}:
                continue
            # split link name to protocol, sender, receiver
            sender = LINK_NAME_TO_TX_NAME(link_name)
            prot = LINK_NAME_TO_PROT_NAME(link_name)
            receiver = LINK_NAME_TO_RX_NAME(link_name)
            if receiver:
                ip_addr = graph.info_graph[receiver][prot + "_ip_addr"]
            else:
                ip_addr = "127.0.0.1"
            conn.batch(
                sender,
                "run-replay-client",
                {
                    "target_addr": ip_addr,
                    "duration": DURATION,
                    "manifest_name": link_name + ".json",
                    "ipc-port": graph.info_graph[sender][link_name][
                        "ipc_port"
                    ],
                },
                timeout= DURATION + 5,
            )

    return conn.executor.wait(DURATION + 5)

def fileTransfer(graph, target_ip, output_folder):
    isSend = False
    conn = Connector()
    import threading
    from tools.file_rx import receiver
    port = 15555
    threading.Thread(target=receiver, args=(target_ip, port, output_folder,)).start()
    for device_name, links in graph.graph.items():
        for link_name, streams in links.items():
            if not isSend:
                prot, sender, receiver = link_name.split("_")
                conn.batch(sender, "send_file", {"target_ip": target_ip, "file_name": "../stream-replay/logs/rtt-*.txt"})
                isSend = True

    conn.executor.wait(0.5).apply()

def rtt_read(graph, opStructs = None):
    conn = Connector()
    for device_name, links in graph.graph.items():
        for link_name, streams in links.items():
            if streams == {}:
                continue
            # split link name to protocol, sender, receiver
            sender = LINK_NAME_TO_TX_NAME(link_name)
            for stream_name, stream_handle in streams.items():
                # extract port number
                if stream_handle.calc_rtt == False:
                    continue
                port_num, tos = stream_name.split("@")
                conn.batch(sender, "read_rtt", {"port": port_num, "tos": tos})
    results = conn.executor.wait(0.5).fetch().apply()
    print('rtt results', results)
    idx = 0
    for device_name, links in graph.graph.items():
        for link_name, streams in links.items():
            if streams == {}:
                continue
            # split link name to protocol, sender, receiver
            for stream_name, stream_handle in streams.items():
                if stream_handle.calc_rtt == False:
                    continue
                data = dataStruct(results[idx])
                if opStructs and len(opStructs) > idx:
                    opStructs[idx].update(data)
                graph.info_graph[device_name][link_name][stream_name].update(
                    {"channel_val": data}
                )
                idx += 1
    return graph

def write_remote_stream(graph: Graph):
    conn = Connector()
    for device_name, links in graph.graph.items():
        for link_name, streams in links.items():
            if streams == {}:
                continue
            sender = LINK_NAME_TO_TX_NAME(link_name)
            idx = 0
            for stream_name, _stream in streams.items():
                if idx == 0:
                    _clear = True
                else:
                    _clear = False
                cmd = create_command(_stream, f'../stream-replay/data/{link_name}.json', clear=_clear)
                conn.batch(sender, 'abuse_manifest', {'cmd': cmd}).wait(0.1)
                idx += 1
    conn.executor.wait(0.1).apply()

def _loop_apply(conn:Connector):
    """
    Continuing apply the connector, fetch the result from remote until receiving outputs
    """
    conn.fetch()
    idx = 0
    while True:
        try:
            # print("try to apply", idx)
            idx += 1
            outputs = conn.apply()
            return outputs
            break
        except Exception as e:
            print(e)
            break