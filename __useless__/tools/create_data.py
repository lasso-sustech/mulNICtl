import numpy as np

def createArgs():
    import argparse
    parser = argparse.ArgumentParser(description='Create data for training')
    parser.add_argument('--thru', type=float, default=50.0,help="Throughput in Mbps")
    parser.add_argument('--arrivalGap', type=float, default=16,help="Arrival gap in ms")
    parser.add_argument('--name', type=str, default="test.npy",help="dataName")
    parser.add_argument('--arrivalVar', type=float, default=0.5, help = "Arrival variance in ms")
    parser.add_argument('--variance', type=float, default=0.1,help="variance in ms")
    parser.add_argument('--num', type=int, default=100,help="packet num")
    args = parser.parse_args()
    return args

time_packet = []

def createData(thru, arrivalGap, variance, arrivalVar, num = 100):
    # Create data
    # arrivalGap in ms -> milliseconds, thru in Mbps -> bytes
    for _ in range(num):
        # gapTime = np.random.lognormal(np.log(arrivalGap) - arrivalVar * arrivalVar / 2, arrivalVar)
        gapTime = arrivalGap
        # gapTime = arrivalGap + np.random.normal(0, variance)
        # gapTime = min(max(0.1, gapTime), arrivalGap * 2)
        ## normal
        # _thru = min(max(0.1, thru + np.random.normal(0, variance)), 5 * thru)
        ## lognormal
        # _thru = np.random.lognormal(np.log(thru) - variance * variance / 2, variance)
        _thru = thru
        time_packet.append([int(gapTime * 1e6), int(_thru * 1e3 * arrivalGap / 8 )])
    return time_packet

args = createArgs()
time_packet = np.array(createData(args.thru, args.arrivalGap, args.variance, args.arrivalVar , args.num)).astype(np.uint64)
np.save(args.name, time_packet)