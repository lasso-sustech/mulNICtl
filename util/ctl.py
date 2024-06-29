import json
import sys
import os
import time
from util.trans_graph import Graph
from util.trans_graph import LINK_NAME_TO_TX_NAME, LINK_NAME_TO_RX_NAME, LINK_NAME_TO_PROT_NAME, LINK_NAME_TO_TX_IF_NAME
from util.solver import dataStruct
from util.stream import stream, create_command
import util.constHead as constHead
from util.api.ipc import ipc_control
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from tap import Connector
from typing import List

## threading component
import queue
import threading
class CtlManager:
    def __init__(self) -> None:
        self.duration = 10
        self.info_queue = queue.Queue()
        pass
    
    def _communication_thread(self, topo:Graph):
        create_tx_manifest(topo)
        time.sleep(1)
        conn        = start_transmission(graph = topo, DURATION = self.duration)
        thrus       = read_thu( conn )
        self.info_queue.put(thrus)
        
    def exp_thread(self, topo:Graph, thread_handles:List[threading.Thread] = []):
        threads = []
        threads.append(threading.Thread(target=self._communication_thread, args=(topo,)))
        for th in thread_handles:
            threads.append(th)
        for th in threads:
            th.start()

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

    conn = Connector()
    channel_table = {}
    for device_name, ips in ip_table.items():
        for if_name, ip in ips.items():
            conn.batch(device_name, "get_channel", {"interface": if_name})
            channel_table.update({device_name: {if_name: None}})
    outputs = conn.executor.wait(1).fetch().apply()
    results = [o["channel_info"] for o in outputs]
    idx = 0
    for device_name, ips in ip_table.items():
        for if_name, ip in ips.items():
            channel_table[device_name][if_name] = results[idx]
            idx += 1
    
    with open("./temp/channel_table.json", "w") as f:
        json.dump(channel_table, f)
    
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

def validate_ip_addr(graph:Graph):
    for device_name, links in graph.graph.items():
        for link_name, streams in links.items():
            if streams == {}:
                continue
            sender = LINK_NAME_TO_TX_NAME(link_name)
            sender_ips = [ v for k, v in graph.info_graph[sender].items() if k.endswith('_ip_addr')]
            idx = 0
            for stream_name, _stream in streams.items():
                for ip_addr in _stream.tx_ipaddrs():
                    if ip_addr not in sender_ips:
                        print(f"Error: {sender} do not have ip address {ip_addr}")
                  
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

def get_ipc_sockets(graph:Graph):
    ipc_handles = {}
    for device_name, links in graph.graph.items():
        for link_name, streams in links.items():
            if streams == {}:
                continue
            ip_addr = graph.info_graph[device_name][LINK_NAME_TO_PROT_NAME(link_name) + "_ip_addr"]
            local_port = graph.info_graph[device_name][link_name]["local_port"]
            ipc_port = graph.info_graph[device_name][link_name]["ipc_port"]
            print(f"device {device_name} with ip {ip_addr} and ipc port {ipc_port}")
            ipc_handles.update({device_name: ipc_control(ip_addr, ipc_port, local_port)})
    return ipc_handles

def config_route(graph:Graph, password:str):
    conn = Connector()
    for device_name, links in graph.graph.items():
        interface_names = set()
        for link_name, streams in links.items():
            if streams == {}:
                continue
            sender = LINK_NAME_TO_TX_NAME(link_name)
            prot = LINK_NAME_TO_PROT_NAME(link_name)
            interface_names.add(prot)
        conn.batch(device_name, "config_network", {"interface_names": list(interface_names), "password": password})
        conn.executor.wait(0.1)
    res = conn.executor.wait(0.1).fetch().apply()
    return res

def read_mcs(graph:Graph):
    conn = Connector()
    for device_name, links in graph.info_graph.items():
        for link_name, streams in links.items():
            try:
                constHead.INTERFACE_INFO_SCHEMA.validate(streams)
            except:
                continue
            sender = LINK_NAME_TO_TX_NAME(link_name)
            ifname = LINK_NAME_TO_TX_IF_NAME(link_name)
            conn.batch(sender, "read_mcs", {"ifname": ifname}).wait(0.1)
    results = conn.executor.wait(0.1).fetch().apply()
    idx = 0
    for device_name, links in graph.info_graph.items():
        for link_name, streams in links.items():
            try:
                constHead.INTERFACE_INFO_SCHEMA.validate(streams)
            except:
                continue
            data = results[idx] # wlx081f7163a94f
            try:
                mcs = float(eval(data.get("mcs_value"))[0])
            except:
                raise ValueError(f'{link_name} do not have mcs, please check 1. topo setting, 2. network connection issue' )
            ifname = LINK_NAME_TO_TX_IF_NAME(link_name)
            graph.info_graph[device_name][link_name].update(
                {"MCS": mcs}
            )
            idx += 1
    return results

def start_transmission(graph:Graph, DURATION):
    """
    Construct a transmission ready connector waiting to be applied
    """
    validate_ip_addr(graph)
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

def read_rtt(graph) -> List[dataStruct]:
    
    conn = Connector()
    opStructs = []
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
    idx = 0
    for device_name, links in graph.graph.items():
        for link_name, streams in links.items():
            if streams == {}:
                continue
            # split link name to protocol, sender, receiver
            for stream_name, stream_handle in streams.items():
                if stream_handle.calc_rtt == False:
                    continue
                try:
                    data = dataStruct(results[idx])
                except:
                    raise ValueError(f'stream {stream_name} transmitted on link {link_name}:\n\t RTT not found, please check: 1. NIC connection 2. port overlapping')
                opStructs.append(data)
                graph.info_graph[device_name][link_name][stream_name].update(
                    {"channel_val": data}
                )
                idx += 1
    return opStructs

def create_tx_manifest(graph: Graph):
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
                # print(f"create manifest for {sender} with cmd {cmd}")
                conn.batch(sender, 'abuse_manifest', {'cmd': cmd}).wait(0.1)
                idx += 1
    conn.executor.wait(0.1).apply()
    time.sleep(0.1)

def read_thu(conn:Connector):
    """
    Continuing apply the connector, fetch the result from remote until receiving outputs
    """
    conn.fetch()
    idx = 0
    maximum_retry = 5
    while True:
        try:
            # print("try to apply", idx)
            idx += 1
            outputs = conn.apply()
            return outputs
            break
        except Exception as e:
            print(e)
            if idx >= maximum_retry:
                break
            continue
        
def clean_up_receiver(graph: Graph, password:str):
    conn = Connector()
    for device_name, links in graph.graph.items():
        for link_name, streams in links.items():
            if streams == {}:
                continue
            receiver = LINK_NAME_TO_RX_NAME(link_name)
            conn = Connector()
            conn.batch(receiver, "clean_up_rx",{'password': password})
            conn.executor.wait(0.1)
    conn.executor.wait(0.1).apply()
    time.sleep(0.1)