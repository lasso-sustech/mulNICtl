# import dataStruct

import numpy as np
from typing import List

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from util.solver import opStruct
import json

import matplotlib.pyplot as plt

def read_chan_rtt(data: opStruct):
    '''
    Read channel rtt from data
    '''
    cha_rtt = np.array(data.channel_rtts)
    diff = cha_rtt[0] - cha_rtt[1]
    if any(cha_rtt == 0):
        return np.sign(cha_rtt) * data.rtt
    if diff > 0:
        return np.array([ data.rtt, data.rtt - diff ])
    else:
        return np.array([ data.rtt + diff, data.rtt ])

def line_infer(datas: List[opStruct], channel: int = 0):
    cha_rtts = []
    for data in datas:
        cha_rtts.append(read_chan_rtt(data))
    
    # assert(cha_rtts[0][channel] != 0)
    # Calculate the slope
    slope = (cha_rtts[1][channel] - cha_rtts[0][channel]) / (datas[1].tx_parts[channel] - datas[0].tx_parts[channel])

    # Calculate the intercept
    intercept = cha_rtts[0][channel] - slope * datas[0].tx_parts[channel]

    # Predict DATA for the rest data
    predicted = []
    for data in datas:
        predicted.append(slope * data.tx_parts[channel] + intercept)
    
    return predicted

def rtt_distance_cal(datas: List[opStruct], channel: int = 0):
    cha_rtts = []
    for data in datas:
        cha_rtts.append(read_chan_rtt(data))

    predicted = line_infer(datas, channel)
    distances = []
    for i in range(len(predicted)):
        distances.append(cha_rtts[i][channel] - predicted[i])
    return distances

def load_data(file_path: str) -> List[opStruct]:
    '''
    Load data from file
    '''
    with open(file_path, 'r') as f:
        datas = json.load(f)
        for i in range(len(datas)):
            datas[i] = opStruct().load_from_dict(datas[i])
    return datas

def line_plot( data_x , data_list, label = ''):
    plt.plot(data_x, data_list, label=label, marker='o')

channel = 1
datas = load_data('../logs/2024-3-26/OneTask2.json')

if channel == 1:
    datas = datas[1:]
else:
    datas = datas[:-1]
# datas = datas[::-1]

# print(read_chan_rtt(datas))

data_x = [ data.tx_parts[0] for data in datas]
channel_rtt = [read_chan_rtt(data)[channel] for data in datas]
infered_rtt = line_infer(datas, channel)
print(channel_rtt)

line_plot(data_x, np.abs(np.array(rtt_distance_cal(datas, channel))) * 1000, 'Error')
line_plot(data_x, np.array(channel_rtt) * 1000, 'Real')
line_plot(data_x, np.array(infered_rtt) * 1000, 'Infered')

plt.xlabel('2.4G Transmission Part')
plt.ylabel('Error (ms)')
channel_str = '2.4G' if channel == 1 else '5G'
plt.title(f'Channel {channel_str} RTT Error')
plt.legend()
plt.savefig('test2.png')