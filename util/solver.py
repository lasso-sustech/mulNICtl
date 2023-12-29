import json
class dataStruct:
    def __init__(self, rttDict):
        self.channel_rtts = [rttDict['rtt'][1], rttDict['rtt'][2]]
        self.channel_probabilities = [rttDict['rtt'][3], rttDict['rtt'][4]]

    def __str__(self) -> str:
        return json.dumps(self.__dict__, indent=2)
    
    def to_dict(self):
        return self.__dict__

    
class opStruct:
    def __init__(self):
        self.min_step = 0.05
        self.tx_parts = [1,1] # [100% send by tx1, 0% send by tx2]
        self.inc_direction = [1, -1]
        self.channel_rtts = [0, 0]
        self.channel_probabilities = [0 , 0]
        self.epsilon_rtt = 0.1
        self.epsilon_prob_upper = 0.3 # probability that packet send all the packet
        self.epsilon_prob_lower = 0.1  # probability that packet do not send all the packet

    def update(self, data:dataStruct):
        self.channel_rtts = data.channel_rtts
        self.channel_probabilities = data.channel_probabilities
        return self

    def load_balance(self):
        assert(self.tx_parts[0] == self.tx_parts[1])
        if abs(self.channel_rtts[0] - self.channel_rtts[1]) < self.epsilon_rtt:
            return self
        else:
            self.tx_parts[0] += self.min_step if self.channel_rtts[0] < self.channel_rtts[1] else -self.min_step
            self.tx_parts[1] = self.tx_parts[0]
            return self
    
    def extend_load_balance(self):
        for idx, pro in enumerate(self.probability_feedback):
            assert 0 <= pro <= 1
            if pro > self.epsilon_prob_upper:
                self.tx_parts[idx] += self.min_step * self.inc_direction[idx]
            elif pro < self.epsilon_prob_lower:
                self.tx_parts[idx] -= self.min_step * self.inc_direction[idx]
            self.tx_parts[idx] = max(0, min(1, self.tx_parts[idx]))