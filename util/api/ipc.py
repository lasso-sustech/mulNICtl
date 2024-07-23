#!/usr/bin/env python3
import socket
import argparse
import json

import util.constHead as constHead

class ipc_socket():
    def __init__(self, ip_addr, ipc_port, local_port=12345, link_name=""):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 196)
        self.sock.settimeout(1.5)
        self.sock.bind(("0.0.0.0", local_port))
        self.link_name = link_name
        self.ip_addr = ip_addr
        self.ipc_port = ipc_port

    def send_cmd(self, *args):
        cmd = args[0]
        body = args[1]
        message = {"cmd": {cmd: body}}        
        server_address = (self.ip_addr, self.ipc_port)
        message = json.dumps(message)
        self.sock.sendto(message.encode(), server_address)
    
    def ipc_communicate(self, *args):
        self.send_cmd(*args)
        _buffer, addr = self.sock.recvfrom(2048)
        return _buffer
    
    def ipc_transmit(self, *args):
        self.send_cmd(*args)
        
    def close(self):
        self.sock.close()
        
class ipc_control(ipc_socket):
    def __init__(self, ip_addr, ipc_port, local_port=12345, link_name=""):
        super().__init__(ip_addr, ipc_port, local_port, link_name)
    
    def throttle(self, throttle_ctl):
        constHead.throttle_control_schema.validate(throttle_ctl)
        self.ipc_transmit('Throttle', throttle_ctl)
        return None

    def statistics(self):
        res = self.ipc_communicate('Statistics', {})
        return res
    
    def tx_part(self, tx_part):
        constHead.tx_part_control_schema.validate(tx_part)
        self.ipc_transmit('TxPart', tx_part)
        return None
    
    def release(self):
        self.close()
        return None