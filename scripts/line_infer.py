# import dataStruct

import numpy as np
from typing import List

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from util.solver import channelBalanceSolver
import json

import matplotlib.pyplot as plt

def read_chan_rtt(data: channelBalanceSolver):
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

def line_infer(datas: List[channelBalanceSolver], channel: int = 0):
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

def line_infer_func(datas: List[channelBalanceSolver], channel: int = 0) -> callable:
    cha_rtts = []
    for data in datas:
        cha_rtts.append(read_chan_rtt(data))
    
    # assert(cha_rtts[0][channel] != 0)
    # Calculate the slope
    slope = (cha_rtts[1][channel] - cha_rtts[0][channel]) / (datas[1].tx_parts[channel] - datas[0].tx_parts[channel])

    # Calculate the intercept
    intercept = cha_rtts[0][channel] - slope * datas[0].tx_parts[channel]

    # Predict DATA for the rest data
    def infer_func(tx_part):
        return slope * tx_part + intercept
    
    print(f'Channel {channel} Infer Func: {slope * 1000} * x + {intercept * 1000}')
    return infer_func

def find_minimum_part(func1, func2):
    minimum_part = 0
    minimum_diff = 1000000
    maximum_part_num = 100
    for part in range(0, maximum_part_num):
        _part = part / maximum_part_num
        if abs(func1(_part) - func2(_part)) < minimum_diff:
            minimum_diff = abs(func1(_part) - func2(_part))
            minimum_part = _part
    return minimum_part

def rtt_distance_cal(datas: List[channelBalanceSolver], channel: int = 0):
    cha_rtts = []
    for data in datas:
        cha_rtts.append(read_chan_rtt(data))

    predicted = line_infer(datas, channel)
    distances = []
    for i in range(len(predicted)):
        distances.append(cha_rtts[i][channel] - predicted[i])
    return distances

def load_data(file_path: str) -> List[channelBalanceSolver]:
    '''
    Load data from file
    '''
    with open(file_path, 'r') as f:
        datas = json.load(f)
        for i in range(len(datas)):
            datas[i] = channelBalanceSolver().load_from_dict(datas[i])
    return datas

def line_plot( data_x , data_list, label = ''):
    plt.plot(data_x, data_list, label=label, marker='o')

if __name__ == '__main__':
    ## Plot Script 1
    # channel = 0
    # datas = load_data('../logs/2024-3-26/test1.json')

    # if channel == 1:
    #     datas = datas[1:]
    # else:
    #     datas = datas[:-1]
    # # datas = datas[::-1]

    # # print(read_chan_rtt(datas))

    # data_x = [ data.tx_parts[0] for data in datas]
    # channel_rtt = [read_chan_rtt(data)[channel] for data in datas]
    # infered_rtt = line_infer(datas, channel)
    # print(channel_rtt)

    # line_plot(data_x, np.abs(np.array(rtt_distance_cal(datas, channel))) * 1000, 'Error')
    # line_plot(data_x, np.array(channel_rtt) * 1000, 'Real')
    # line_plot(data_x, np.array(infered_rtt) * 1000, 'Infered')

    # plt.xlabel('2.4G Transmission Part')
    # plt.ylabel('Error (ms)')
    # channel_str = '2.4G' if channel == 1 else '5G'
    # plt.title(f'Channel {channel_str} RTT Error')
    # plt.legend()
    # plt.savefig('test5.png')

    ## Result Display 1
    import csv
    # datas = load_data('../logs/2024-3-26/test1.json')
    # datas = load_data('../logs/2024-3-26/Predict Res 7 - throughput 400.json')
    # datas = load_data('../logs/2024-3-26/Predict Res 6 - throughput 100.json')
    datas = load_data('../logs/2024-3-26/Predict Res 5 - throughput 200.json')
    # datas = load_data('../logs/2024-3-26/Predict Res 4 - throughput 300.json')
    csv_file = open('test1.csv', 'w')
    device_num = 2
    csv_file.write(f'2.4G Part, Taks1 - 5G, Taks1 - channel 2.4G, Taks2 - channel 5G, Taks2 - channel 2.4G \n')
    for i in range(len(datas) // device_num):
        csv_file.write(f'{datas[i * device_num].tx_parts[0] * 100:.0f},')
        for j in range(device_num):
            channel_rtt = read_chan_rtt(datas[i * device_num + j]) * 1000

            print(f'device {j}, 2.4 Part {datas[i * device_num + j].tx_parts[0]}: 5G {channel_rtt[0]:.3f} ms, 2.4G {channel_rtt[1]:.3f} ms')
            csv_file.writelines(f'{read_chan_rtt(datas[i * device_num + j])[0] * 1000},{read_chan_rtt(datas[i * device_num + j])[1] * 1000},')
        csv_file.write('\n')
        print('')
    
    datas = np.array(datas).reshape(-1, device_num).T
    channel = 2
    csv_file.write(f'{datas[0][-1].tx_parts[0] * 100:.0f},')
    for i in range(device_num):
        inter_funcs = [ line_infer_func(datas[i], _channel) for _channel in range(channel) ]


        part = datas[i][-1].tx_parts[0]

        rtt = max([inter_funcs[_channel](part) for _channel in range(channel)])
        print(f'Predict device {i}, 2.4 Part {part}: {[inter_funcs[_channel](part) for _channel in range(channel)]}')
        [csv_file.write(f'{inter_funcs[_channel](part) * 1000},') for _channel in range(channel)]
