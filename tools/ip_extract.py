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
        keyword = 'wlan0'
        res = re.search(r'wlan0:[^\n]*\n\s*inet\s+(\d{1,3}(?:\.\d{1,3}){3})', res)
        if res:
            info.append((keyword, res.group(1)))
    return info

print(get_ip())