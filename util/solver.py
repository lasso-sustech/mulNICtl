import json
class dataStruct:
    def __init__(self, rttDict):
        self.data_frac = float(rttDict['rtt'][0])
        self.rtt = float(rttDict['rtt'][1])
        self.channel_rtts = [float(rttDict['rtt'][2]), float(rttDict['rtt'][3])]
        self.channel_probabilities = [float(rttDict['rtt'][4]), float(rttDict['rtt'][5])]

    def __str__(self) -> str:
        return json.dumps(self.__dict__, indent=2)
    
    def to_dict(self):
        return self.__dict__

    
class opStruct:
    def __init__(self):
        self.min_step = 0.05
        self.data_frac = 0
        self.rtt = 0
        self.tx_parts = [1,1] # [100% send by tx1, 0% send by tx2]
        self.inc_direction = [-1, 1]
        self.channel_rtts = [0, 0]
        self.channel_probabilities = [0 , 0]
        self.epsilon_rtt = 0.001 # 1ms
        self.epsilon_prob_upper = 0.3 # probability that packet send all the packet
        self.epsilon_prob_lower = 0.1  # probability that packet do not send all the packet

    def update(self, data:dataStruct):
        self.data_frac = data.data_frac
        self.rtt = data.rtt
        self.channel_rtts = data.channel_rtts
        self.channel_probabilities = data.channel_probabilities
        return self
    
    def update_tx_parts(self, tx_parts):
        self.tx_parts = tx_parts
        return self

    def load_balance(self):
        assert(self.tx_parts[0] == self.tx_parts[1])
        if abs(self.channel_rtts[0] - self.channel_rtts[1]) < self.epsilon_rtt:
            return self
        else:
            self.tx_parts[0] += self.min_step if self.channel_rtts[0] < self.channel_rtts[1] else -self.min_step
            self.tx_parts[0] = round(self.tx_parts[0], 2)
            self.tx_parts[1] = self.tx_parts[0]
            return self
    
    def check_load_balance(self):
        return abs(self.channel_rtts[0] - self.channel_rtts[1]) < self.epsilon_rtt
    
    def extend_load_balance(self):
        for idx, pro in enumerate(self.channel_probabilities):
            assert 0 <= pro <= 1
            if pro > self.epsilon_prob_upper:
                self.tx_parts[idx] += self.min_step * self.inc_direction[idx]
            elif pro < self.epsilon_prob_lower:
                self.tx_parts[idx] -= self.min_step * self.inc_direction[idx]
            self.tx_parts[idx] = round(max(0, min(1, self.tx_parts[idx])),2)

    def apply(self, _stream):
        _stream.tx_parts = self.tx_parts
        return _stream
    
    def __str__(self) -> str:
        return json.dumps(self.__dict__, indent=2)