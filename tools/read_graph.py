import re
import sys; import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
from util.trans_graph import Graph
'''
STA1 --WIFI5G-- SoftAP
STA1 --WIFI2.4G-- SoftAP
STA2 --WIFI-- SoftAP
'''
PATTERN = re.compile(r'\b\w+\b')

def construct_graph(file_path):
    links = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
        graph = Graph()
        for line in lines:
            line = re.findall(PATTERN, line.strip())
            if len(line) >= 3:
                start = line[0]; end = line[-1]
                link = '_'.join(line[1:-1])
                link_name = graph.ADD_LINK(start, end, link,  '600')
                links.append(link_name)
    return graph, links