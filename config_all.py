#!/usr/bin/env python3
import json
from tap import Connector
import util.ctl as ctl 
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--password', type=str, required=True)
args = parser.parse_args()

## Default sync
from tools.read_graph import construct_graph

topo        = construct_graph("./config/topo/2024-5-9.txt")
ctl.config_route(topo, args.password)
