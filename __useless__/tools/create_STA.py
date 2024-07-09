import re
import subprocess
import sys; import os
current = os.path.dirname(os.path.realpath(__file__))
'''
STA1 --WIFI5G-- SoftAP
STA1 --WIFI2.4G-- SoftAP
STA2 --WIFI-- SoftAP
'''
PATTERN = re.compile(r'\b\w+\b')

def parse_sta(file_path, addr):
    sta_set = set()
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = re.findall(PATTERN, line.strip())
            if len(line) >= 3:
                start = line[0]; end = line[-1]
                ## verify
                if '_' in start or '_' in end:
                    print(f'Error: {start} or {end} is not a valid name')
                    sys.exit(1)
                sta_set.add(start); sta_set.add(end)

    for sta in sta_set:
        subprocess.Popen(['gnome-terminal', '-e', f'python3 tap.py -c {addr} -n {sta}'])


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='file path', default='./config/lo.txt')
    parser.add_argument('-a', '--addr', help='controller addr', default='127.0.0.1')
    args = parser.parse_args()
    parse_sta(args.file, args.addr)
    
