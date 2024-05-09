import json
import numpy as np

from util.predictor import rttPredictor
import util.constHead as constHead
from util.qos import get_mul_chan_qos, get_proj_qos
from typing import List

class dataStruct:
    def __init__(self, rttDict, scale = 1000):
        self.data_frac = float(rttDict["rtt"][0])
        self.rtt = float(rttDict["rtt"][1]) * scale
        self.channel_rtts = [
            float(rttDict["rtt"][2]) * scale,
            float(rttDict["rtt"][3]) * scale,
        ]
        self.channel_rtts = self.correct_channel_rtt()
        self.channel_probabilities = [
            float(rttDict["rtt"][4]),
            float(rttDict["rtt"][5]),
        ]

    def correct_channel_rtt(self):
        channel_rtts = []
        if self.channel_rtts[0] == 0:
            return [0, self.rtt]
        if self.channel_rtts[1] == 0:
            return [self.rtt, 0]
        rtt_diff = self.channel_rtts[0] - self.channel_rtts[1]
        if rtt_diff >= 0:
            channel_rtts = [self.rtt, self.rtt - rtt_diff]
        elif rtt_diff < 0:
            channel_rtts = [self.rtt + rtt_diff, self.rtt]
        return channel_rtts

    def __str__(self) -> str:
        return json.dumps(self.__dict__, indent=2)

    def to_dict(self):
        return self.__dict__

class channelBalanceSolver:
    def __init__(self):
        self.min_step = 0.05
        self.rtt = 0
        self.tx_parts = [1,1] # [100% send by tx1, 0% send by tx2]
        self.inc_direction = [-1, 1]
        self.channel_rtts = [0, 0]
        self.channel_probabilities = [0 , 0]
        self.epsilon_rtt = 0.5 # 10%
        self.epsilon_prob_upper = 0.6 # probability that packet send all the packet
        self.epsilon_prob_lower = 0.01  # probability that packet do not send all the packet

    def __add__(self, other):
        if isinstance(other, channelBalanceSolver):
            assert(self.tx_parts[0] == other.tx_parts[0] and self.tx_parts[1] == other.tx_parts[1])
            self.rtt += other.rtt
            self.channel_rtts = [x + y for x, y in zip(self.channel_rtts, other.channel_rtts)]
            self.channel_probabilities = [x + y for x, y in zip(self.channel_probabilities, other.channel_probabilities)]
        return self
    
    def __truediv__(self, fraction):
        assert(fraction > 0)
        self.rtt /= fraction
        self.channel_rtts = [x / fraction for x in self.channel_rtts]
        self.channel_probabilities = [x / fraction for x in self.channel_probabilities]
        return self
    
    def correct_channel_rtt(self):
        channel_rtts = []
        if self.channel_rtts[0] == 0:
            return [0, self.rtt]
        if self.channel_rtts[1] == 0:
            return [self.rtt, 0]
        rtt_diff = self.channel_rtts[0] - self.channel_rtts[1]
        if rtt_diff >= 0:
            channel_rtts = [self.rtt, self.rtt - rtt_diff]
        elif rtt_diff < 0:
            channel_rtts = [self.rtt + rtt_diff, self.rtt]
        return channel_rtts

    def update(self, qos):
        constHead.PROJ_QOS_SCHEMA.validate(qos)
        self.rtt = qos["rtt"]
        self.channel_rtts = qos["channel_rtts"]
        self.channel_probabilities = qos["channel_probabilities"]
        return self
    
    def update_tx_parts(self, tx_parts):
        self.tx_parts = tx_parts
        return self

    def solve_by_rtt_balance(self):
        assert(self.tx_parts[0] == self.tx_parts[1])
        if abs(self.channel_rtts[0] - self.channel_rtts[1]) < self.epsilon_rtt:
            constHead.TX_PARTS_SCHEMA.validate(self.tx_parts)
            return self
        else:
            self.tx_parts[0] += self.min_step if self.channel_rtts[0] > self.channel_rtts[1] else -self.min_step
            self.tx_parts[0] = max(0, min(1, self.tx_parts[0]))
            self.tx_parts[0] = round(self.tx_parts[0], 2)
            self.tx_parts[1] = self.tx_parts[0]
            constHead.TX_PARTS_SCHEMA.validate(self.tx_parts)
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
        constHead.TX_PARTS_SCHEMA.validate(self.tx_parts)
        return self
        
    def apply(self, _stream):
        _stream.tx_parts = self.tx_parts
        return _stream
    
    def __str__(self) -> str:
        return json.dumps(self.__dict__, indent=2)
    
    def load_from_dict(self, _dict):
        for key, value in _dict.items():
            setattr(self, key, value)
        constHead.TX_PARTS_SCHEMA.validate(self.tx_parts)
        return self

class channelSwitchSolver:
    def __init__(self, target_rtt = 16, channel_idx = 0) -> None:
        self.rtt_predict = rttPredictor()
        self.target_rtt = target_rtt # ms
        self.switch_state = constHead.CHANNEL0
        self.islog = False
    
    def print_log(self, log):
        if self.islog:
            print(log)
            
    def is_backward_switch_able(self):

        tx_parts = [0, 0]
        predicted_val = self.rtt_predict.predict(tx_parts)
        self.print_log(f"Predicted CH1 RTT: {predicted_val[0]}, Target RTT: {self.target_rtt}")
        channel_0_val = predicted_val[0]
        
        tx_parts = [1, 1]
        predicted_val = self.rtt_predict.predict(tx_parts)
        self.print_log(f"Predicted CH2 RTT: {predicted_val[1]}, Target RTT: {self.target_rtt}")
        channel_1_val = predicted_val[1]
        
        if predicted_val[0] < self.target_rtt and channel_1_val > self.target_rtt:
            self.switch_state = constHead.CHANNEL0
            return self
        
        elif predicted_val[1] < self.target_rtt and channel_0_val > self.target_rtt:
            self.switch_state = constHead.CHANNEL1
            return self
        
        elif channel_0_val <= channel_1_val and channel_1_val <= self.target_rtt:
            self.switch_state = constHead.CHANNEL0
            return self
        elif channel_1_val <= channel_0_val and channel_0_val <= self.target_rtt:
            self.switch_state = constHead.CHANNEL1
            return self
        
        self.print_log(f"Predicted RTT: {predicted_val[0]}, {predicted_val[1]}, Target RTT: {self.target_rtt}")      
        return self
    
    def switch(self, tx_parts, channel_rtt):
        def is_rtt_satisfy(rtt):
            return rtt < self.target_rtt
        
        self.rtt_predict.update(tx_parts, channel_rtt)
                
        if (not is_rtt_satisfy(channel_rtt[0]) and channel_rtt[1] == 0) or (not is_rtt_satisfy(channel_rtt[1]) and channel_rtt[0] == 0):
            self.switch_state = constHead.MUL_CHAN
        
        if all(is_rtt_satisfy(rtt) for rtt in channel_rtt) and self.switch_state == constHead.MUL_CHAN:
            try:
                return self.is_backward_switch_able()
            except Exception as e:
                print(e)
        
        return self
class singleDirFlowTransSolver:
    def __init__(self, direction) -> None:
        self.direction = direction
        assert direction in [constHead.FLOW_TRANSFER_TO_CHANNEL0, constHead.FLOW_TRANSFER_TO_CHANNEL1, constHead.FLOW_STOP]

    def compute_efficiency_index(self, qos):
        constHead.PROJ_QOS_SCHEMA.validate(qos)
        assert constHead.CHANNEL_RTTS in qos

        channel_rtt = qos[constHead.CHANNEL_RTTS]
        thru = qos[constHead.THRU]
        tx_parts = qos[constHead.TX_PARTS]
        channel_thru = [thru * tx for tx in tx_parts]

        channel_efficiencies = [channel_thru[idx] / channel_rtt[idx] for idx in range(2)]

        if self.direction == constHead.FLOW_TRANSFER_TO_CHANNEL0:
            return channel_efficiencies[1] / channel_efficiencies[0]

        return channel_efficiencies[0] / channel_efficiencies[1]

    def compute_RTT_gap(self, qos):
        constHead.PROJ_QOS_SCHEMA.validate(qos)
        if len(qos['channels']) == 1:
            if (
                self.direction == constHead.FLOW_TRANSFER_TO_CHANNEL0
                and qos["channels"][0] == constHead.CHANNEL0
            ):
                return qos["target_rtt"] - qos["rtt"]
            if (
                self.direction == constHead.FLOW_TRANSFER_TO_CHANNEL1
                and qos["channels"][0] == constHead.CHANNEL1
            ):
                return qos["target_rtt"] - qos["rtt"]

        if constHead.CHANNEL_RTTS in qos:
            if constHead.FLOW_TRANSFER_TO_CHANNEL0:
                return qos['target_rtt'] - qos[constHead.CHANNEL_RTTS][0]
            return qos['target_rtt'] - qos[constHead.CHANNEL_RTTS][1]

    def compute_propose_flow_thru(self, qos, upperbound):
        constHead.PROJ_QOS_SCHEMA.validate(qos)
        assert 'channel_rtt' in qos

        channel_rtt = qos['channel_rtt']
        thru = qos[constHead.THRU]
        tx_parts = qos[constHead.TX_PARTS]
        channel_thru = [thru * tx for tx in tx_parts]

        if self.direction == constHead.FLOW_TRANSFER_TO_CHANNEL0:
            return min(channel_rtt[1], upperbound) * channel_thru[1] / channel_rtt[1]

        return min(channel_rtt[0], upperbound) * channel_thru[0] / channel_rtt[0]

    def compute_predict_rtt_space_change(self, qos, eff):
        constHead.PROJ_QOS_SCHEMA.validate(qos)
        assert 'channel_rtt' in qos

        channel_rtt = qos['channel_rtt']
        thru = qos[constHead.THRU]
        tx_parts = qos[constHead.TX_PARTS]
        channel_thru = [thru * tx for tx in tx_parts]

        if self.direction == constHead.FLOW_TRANSFER_TO_CHANNEL0:
            return channel_thru[1] / eff

        return channel_thru[0] / eff

    def flow_thru_to_control(self, qos, flow_thru):
        constHead.PROJ_QOS_SCHEMA.validate(qos)
        thru = qos[constHead.THRU]
        tx_parts = qos[constHead.TX_PARTS]
        transfered_part = flow_thru / thru
        if self.direction == constHead.FLOW_TRANSFER_TO_CHANNEL0:
            return [tx_parts[0] - transfered_part, tx_parts[1] - transfered_part]

        return [tx_parts[0] + transfered_part, tx_parts[1] + transfered_part]

    def solve(self, qos_list: list):
        qos_list = get_proj_qos(qos_list)
        mul_qos_list = get_mul_chan_qos(qos_list)
        channel_controls = [
            constHead.CHANNEL_CONTROL_SCHEMA.validate(qos) for qos in mul_qos_list
        ]

        if self.direction == constHead.FLOW_STOP:
            return channel_controls

        efficiencies        =   np.array([self.compute_efficiency_index(qos) for qos in mul_qos_list])

        if len(efficiencies) == 0:
            return []

        sorted_efficiencies, sorted_idx = zip(*sorted(zip(efficiencies, range(len(efficiencies)))))

        rtt_gap = [ self.compute_RTT_gap(qos_list[idx]) for idx in sorted_idx   ]
        assert all(_rtt_gap >= 0 for _rtt_gap in rtt_gap) 
        min_rtt_gap = min(rtt_gap)

        transfer_upper_bound = efficiencies * min_rtt_gap

        for idx, (eff, uperbound) in enumerate(zip(sorted_efficiencies, transfer_upper_bound)):
            orginal_idx = sorted_idx[idx]
            propose_flow_thru = self.compute_propose_flow_thru(
                mul_qos_list[orginal_idx], uperbound
            )
            channel_controls[orginal_idx].update(
                {
                    "tx_parts": self.flow_thru_to_control(
                        mul_qos_list[orginal_idx], propose_flow_thru
                    )
                }
            )
            min_rtt_gap -= self.compute_predict_rtt_space_change(
                mul_qos_list[orginal_idx], eff
            )
            if min_rtt_gap < 0:
                break

        for control in channel_controls:
            constHead.CHANNEL_CONTROL_SCHEMA.validate(control)

        return channel_controls

class gb_state:
    def __init__(self) -> None:
        self.state = [None, None]
        
    def update_gb_state(self, qoses):
        channel_lights = [None, None]
        qoses = get_proj_qos(qoses)
        for qos in qoses:
            constHead.PROJ_QOS_SCHEMA.validate(qos)
            
            if qos[constHead.CHANNEL_RTTS][0] > qos['target_rtt']:
                channel_lights[0] = constHead.RED_LIGHT
            if qos[constHead.CHANNEL_RTTS][1] > qos['target_rtt']:
                channel_lights[1] = constHead.RED_LIGHT
                
        if channel_lights[0] is None:
            channel_lights[0] = constHead.GREEN_LIGHT
        if channel_lights[1] is None:
            channel_lights[1] = constHead.GREEN_LIGHT
        self.state = channel_lights
        return self
    
    def get_gb_state(self):
        return self.state
            
    def flow_flag(self):
        if self.state[0] == constHead.RED_LIGHT and self.state[1] == constHead.GREEN_LIGHT:
            return constHead.FLOW_TRANSFER_TO_CHANNEL1
        if self.state[1] == constHead.RED_LIGHT and self.state[0] == constHead.GREEN_LIGHT:
            return constHead.FLOW_TRANSFER_TO_CHANNEL0
        return constHead.FLOW_STOP
    
    def policy(self):
        actions = {
            constHead.FLOW_DIR: self.flow_flag()
        }
        constHead.GB_CONTROL_SCHEMA.validate(actions)
        return actions
