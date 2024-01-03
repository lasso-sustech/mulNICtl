import json
import os
import argparse
'''
"type": "UDP",
"npy_file": "cast_3.125MB.npy",
"tos": 96,
"port": 6201,
"throttle": 0,
"start_offset": 0,
"priority": "",
"calc_rtt": true,
"no_logging": true,
"tx_ipaddrs": [
    "192.168.3.12",
    "192.168.3.14"
],
"tx_parts": [
    0.1,
    0.9
]
'''
CONTENT = {
    "window_size": 500,
    "tx_ipaddrs": [],
    'streams': []
}
class stream:
    def __init__(self) -> None:
        self.type = "UDP"
        self.npy_file = "cast_3.125MB.npy"
        self.tos = 96 # 128
        self.port = 6201
        self.throttle = 0
        self.start_offset = 0
        self.priority = ""
        self.calc_rtt = True
        self.no_logging = True
        self.tx_ipaddrs = [
            "192.168.3.12",
            "192.168.3.14"
        ]
        self.tx_parts = [
            0.1,
            0.9
        ]

    def __str__(self) -> str:
        return json.dumps(self.__dict__, indent=2)
    
    def to_dict(self):
        return self.__dict__
    
    def write_to_manifest(self, file_addr, clear):
        if clear or not os.path.exists(file_addr) or os.path.getsize(file_addr) == 0:
            with open(file_addr, 'w') as f:
                json.dump(CONTENT,f, indent=2)
        with open(file_addr, 'r') as f:
            content = json.load(f)
        content['streams'].append(self.__dict__)
        content['tx_ipaddrs'] = list(set(content['tx_ipaddrs']+self.tx_ipaddrs))
        with open(file_addr, 'w') as f:
            json.dump(content, f, indent=2)
    
    def read_from_manifest(self, file_addr):
        with open(file_addr, 'r') as f:
            content = json.load(f)
        stream_param = content['streams']
        for i in stream_param:
            if i in self.__dict__:
                self.__setattr__(i, stream_param[i])
            else:
                print(f'Warning: {i} not found in stream')
        return self

def create_parse(parser: argparse.ArgumentParser):
    temp = stream()
    for i in temp.__dict__:
        if type(temp.__getattribute__(i)) == list:
            parser.add_argument('--'+i, type=type(temp.__getattribute__(i)[0]), nargs='+', default=temp.__dict__[i])
        else:
            parser.add_argument('--'+i, type=type(temp.__getattribute__(i)), default=temp.__dict__[i])
    return parser 

def create_command(stream: stream, file_addr: str, clear: bool = False):
    command = f'cd util; python3 stream.py --file {file_addr}'
    for i in stream.__dict__:
        if i == 'priority':
            continue
        if type(stream.__getattribute__(i)) == list:
            command += ' --'+i
            for j in stream.__getattribute__(i):
               command += ' '+str(j)
        else:
            command += ' --'+i+' '+str(stream.__getattribute__(i))
    if clear:
        command += ' --clear'
    return command

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=str, default='temp.json')
    parser.add_argument('--clear', action='store_true', default=False)
    parser = create_parse(parser)
    args = parser.parse_args()
    temp = stream()
    for i in temp.__dict__:
        temp.__setattr__(i, args.__getattribute__(i))
    temp.write_to_manifest(args.file, args.clear)


            