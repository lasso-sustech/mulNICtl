#!/usr/bin/env python3
import re
import sys
import psutil
import os

## init ip information
def get_ip():
    info = []
    try:
        addrs = psutil.net_if_addrs()
        for key in addrs.keys():
            for addr in addrs[key]:
                if addr.family == 2:
                    info.append((key, addr.address))
    except Exception as e:
        ## android might not supported by psutil
        res = os.popen('ifconfig').read()
        for keyword in ['wlan0', 'p2p0', 'lo']:
            # Updated regular expression pattern to handle variations in spacing and formatting
            re_pattern = re.compile(rf'{keyword}.*?\n\s*inet\s+(\d{{1,3}}(?:\.\d{{1,3}}){{3}})', re.S)
            vres = re.search(re_pattern, res)
            if vres:
                info.append((keyword, vres.group(1)))
    return info

print(get_ip())