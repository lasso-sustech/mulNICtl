import numpy as np
def mean_of_quantile(rtts):
    rtts = np.array(rtts)
    rtts = rtts[rtts != 0]
    if len(rtts) == 0:
        return 0
    percent_25 = np.percentile(rtts, 25)
    percent_75 = np.percentile(rtts, 50)
    
    mean_value = np.mean([i for i in rtts if percent_25 <= i <= percent_75])
    return mean_value
    
def read_rtt(file_addr):
    rtt = [[], [], []]
    num = 0
    received = 0
    with open(file_addr, 'r') as f:
        lines = f.readlines()
        received = len(lines)
        for line in lines:
            line = line.strip().split()
            if len(line) >= 3:
                num = int(line[0])
                while len(rtt[0]) < num:
                    rtt[0].append(0)
                    rtt[1].append(0)
                    rtt[2].append(0)
                seq = num - 1
                rtt[0][seq] = max(float(line[1]), rtt[0][seq])
                if float(line[2]) == 10:
                    rtt[1][seq] = float(line[1])
                else:
                    rtt[2][seq] = float(line[1])
                # rtt[1][num].append(float(line[2]))
                # rtt[2][num].append(float(line[3]))
    ## average rtt
    average_rtt = [0,0,0]    
    average_rtt[0] = mean_of_quantile(rtt[0])
    average_rtt[1] = mean_of_quantile(rtt[1])
    average_rtt[2] = mean_of_quantile(rtt[2])
    
    ## probability of non-zero rtt
    probability = [0,0]
    probability[0] = len([i for i in rtt[1] if i != 0])/len(rtt[1])
    probability[1] = len([i for i in rtt[2] if i != 0])/len(rtt[2])

    ## print
    print(f'Received packets fraction: {received/num}')
    print('Average RTT: %.9f %.9f %.9f' % (average_rtt[0], average_rtt[1], average_rtt[2]))
    print(f'Probability of non-zero RTT: {probability}')
    pass

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='file path', default='./temp/rtt.txt')
    args = parser.parse_args()
    read_rtt(args.file)

    