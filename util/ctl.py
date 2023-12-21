import json
from util.trans_graph import Graph
from util.tap import Connector

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

