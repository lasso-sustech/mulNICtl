def read_rtt(file_addr):
    rtt = [[], [], []]
    num = 0
    received = 0
    with open(file_addr, 'r') as f:
        lines = f.readlines()
        received = len(lines)
        for line in lines:
            line = line.strip().split()
            if len(line) >= 4:
                num = float(line[0])
                rtt[0].append(float(line[1]))
                rtt[1].append(float(line[2]))
                rtt[2].append(float(line[3]))
    
    ## average rtt
    average_rtt = [0,0,0]
    average_rtt[0] =  sum(rtt[0])/len(rtt[0])
    # average_rtt[1] = sum(rtt[1])/len(rtt[1])
    # average_rtt[2] = sum(rtt[2])/len(rtt[2])
    average_rtt[1] = len([i for i in rtt[1] if i == 1])/len(rtt[1])
    average_rtt[2] = len([i for i in rtt[2] if i == 1])/len(rtt[2])

    ## probability of non-zero rtt
    probability = [0,0]
    probability[0] = len([i for i in rtt[1] if i != 0])/len(rtt[1])
    probability[1] = len([i for i in rtt[2] if i != 0])/len(rtt[2])

    ## print
    print(f'Received packets fraction: {received/num}')
    print(f'Average RTT: {average_rtt}')
    print(f'Probability of non-zero RTT: {probability}')
    pass

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help='file path', default='./temp/rtt.txt')
    args = parser.parse_args()
    read_rtt(args.file)

    