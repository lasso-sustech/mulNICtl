import json
import os, sys
import argparse

ppath = os.path.join(os.path.dirname(__file__), '..')
if ppath not in sys.path:
    sys.path.append(ppath)
    import util.constHead as constHead

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
        ## None Manifest Variables
        self.target_rtt = 16
        self.channels   = []
        self.name       = ''

    def __str__(self) -> str:
        return json.dumps(self.__dict__, indent=2)
    
    def to_dict(self):
        return self.__dict__
    
    def validate(self):
        with open('temp/ip_table.json', 'r') as f:
            ip_table = json.load(f)
        with open('temp/channel_table.json', 'r') as f:
            channel_table = json.load(f)
            
        if len(set(self.tx_ipaddrs)) > 1:
            for device, ips in ip_table.items():
                for if_name, ip in ips.items():
                    if ip == self.tx_ipaddrs[0]:
                        assert channel_table[device][if_name] == constHead.CHANNEL0, f'{device} {if_name} {channel_table[device][if_name]} {self.tx_ipaddrs[0]} {constHead.CHANNEL0} {self}'
                    if ip == self.tx_ipaddrs[1]:
                        assert channel_table[device][if_name] == constHead.CHANNEL1, f'{device} {if_name} {channel_table[device][if_name]} {self.tx_ipaddrs[1]} {constHead.CHANNEL1} {self}'
            self.channels = [constHead.CHANNEL0, constHead.CHANNEL1]
        else:
            for device, ips in ip_table.items():
                for if_name, ip in ips.items():
                    if ip == self.tx_ipaddrs[0]:
                        self.channels = [channel_table[device][if_name]]
    
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
        if i in ['target_rtt', 'channels', 'name']:
            continue
        if type(temp.__getattribute__(i)) == list:
            parser.add_argument('--'+i, type=type(temp.__getattribute__(i)[0]), nargs='+', default=temp.__dict__[i])
        else:
            parser.add_argument('--'+i, type=type(temp.__getattribute__(i)), default=temp.__dict__[i])
    return parser 

def create_command(stream: stream, file_addr: str, clear: bool = False):
    command = f'cd util; python3 stream.py --file {file_addr}'
    for i in stream.__dict__:
        if i in ['priority', 'target_rtt', 'channels', 'name']:
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
        if hasattr(args, i):
            temp.__setattr__(i, args.__getattribute__(i))
    temp.write_to_manifest(args.file, args.clear)


            