#!/usr/bin/env python3
import re
import sys
import psutil

## init ip information
def get_ip():
    addrs = psutil.net_if_addrs()
    info = []
    for key in addrs.keys():
        for addr in addrs[key]:
            if addr.family == 2:
                info.append((key, addr.address))
                # info[key] = addr.address
    return info

print(get_ip())