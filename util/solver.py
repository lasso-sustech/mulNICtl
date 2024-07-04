import json
import numpy as np

from util.predictor import rttPredictor, thruRTTPredictor
import util.constHead as constHead
from util.trans_graph import Graph, LINK_NAME_TO_TX_IF_NAME
from util.qos import get_mul_chan_qos, get_proj_qos, order_qos, get_file_qos, get_qos_by_name, get_qoss_by_channel, align_qos
from typing import List 

class dataStruct:
    def __init__(self, rttDict, scale = 1000):
        print(f"RTT Dict: {rttDict}")
        self.data_frac = float(rttDict["rtt"][0])
        self.rtt = float(rttDict["rtt"][1]) * scale
        self.channel_rtts = [
            float(rttDict["rtt"][2]) * scale,
            float(rttDict["rtt"][3]) * scale,
        ]
        # self.channel_rtts = self.correct_channel_rtt()
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

class solver:
    def __init__(self, base_info) -> None:
        self.base_info = base_info # Consists of target_rtt, mcs, etc.
        
    def _control(self, qos: List[dict]): #TODO: C implementation
        controls = []
        return controls

    def control(self, qos: List[dict]):
        print(f"QOS: {qos}")
        for q in qos:
            q.update(self.base_info[q['name']])
        controls = self._control(qos)
        for c in controls:
            self.base_info[c['name']].update(c)
        return controls

class balanceSolver(solver):
    def __init__(self, base_info) -> None:
        super().__init__(base_info)
    
    class channelBalanceSolver:
        inc_direction = [-1, 1]
        def __init__(self):
            self.min_step = 0.05
            self.epsilon_rtt = 0.002 # 10%
            self.epsilon_prob_upper = 0.6 # probability that packet send all the packet
            self.epsilon_prob_lower = 0.01  # probability that packet do not send all the packet
            self.redundency_mode = False

        def control(self, qos):
            constHead.PROJ_QOS_SCHEMA.validate(qos)
            if self.redundency_mode:
                return self.redundency_balance(qos)
            return self.solve_by_rtt_balance(qos)

        def solve_by_rtt_balance(self, qos):
            channel_rtts = qos["channel_rtts"]
            tx_parts = qos["tx_parts"]
            assert(len(tx_parts) == 2, "TX parts should have 2 parts")
            assert(tx_parts[0] == tx_parts[1], "In rtt balance mode, TX parts should be the same")
            if any(rtt == 0 for rtt in channel_rtts):
                return tx_parts
            if abs(channel_rtts[0] - channel_rtts[1]) > self.epsilon_rtt:
                tx_parts[0] += self.min_step if channel_rtts[0] > channel_rtts[1] else -self.min_step
                tx_parts[0] = max(0, min(1, tx_parts[0]))
                tx_parts[0] = round(tx_parts[0], 2)
                tx_parts[1] = tx_parts[0]
            constHead.TX_PARTS_SCHEMA.validate(tx_parts)
            return tx_parts

        def redundency_balance(self, qos):
            channel_probabilities = qos["channel_probabilities"]
            tx_parts = qos["tx_parts"]
            for idx, pro in enumerate(channel_probabilities):
                assert 0 <= pro <= 1, f"Invalid probability: {pro}, should be in [0, 1]"
                if pro > self.epsilon_prob_upper:
                    tx_parts[idx] += self.min_step * self.inc_direction[idx]
                elif pro < self.epsilon_prob_lower:
                    tx_parts[idx] -= self.min_step * self.inc_direction[idx]
                tx_parts[idx] = round(max(0, min(1, tx_parts[idx])),2)
            constHead.TX_PARTS_SCHEMA.validate(tx_parts)
            return tx_parts

    def _control(self, qoses):
        controls = []
        for qos in qoses:
            controls.append({
                'name': qos['name'],
                'tx_parts': self.channelBalanceSolver().control(qos),
            })
        return controls

class globalSolver(solver):
    def __init__(self, base_info) -> None:
        super().__init__(base_info)
        self.yellow_fraction = 0.7
        
    def state(self, qoses):
        def light(rtt, target_rtt, yellow_fraction):
            target_rtt = float(target_rtt)
            rtt = float(rtt) * 1000
            if rtt < target_rtt * yellow_fraction:
                return constHead.GREEN_LIGHT
            if rtt < target_rtt:
                return constHead.YELLOW_LIGHT
            return constHead.RED_LIGHT
        
        channel_lights = {}
        qoses = get_proj_qos(qoses)
        for qos in qoses:
            constHead.PROJ_QOS_SCHEMA.validate(qos)
            for channel_rtt, channel in zip(qos[constHead.CHANNEL_RTTS], qos[constHead.CHANNEL]):
                ch_light = light(channel_rtt, qos['target_rtt'], self.yellow_fraction)
                if channel_lights.get(channel) is None:
                    channel_lights[channel] = ch_light
                else:
                    channel_lights[channel] = max(channel_lights[channel], ch_light)
        return channel_lights
    
    def _control(self, qoses):
        channel_lights = self.state(qoses)
        controls = []
        if all(light == constHead.GREEN_LIGHT for light in channel_lights.values()):
            _controls = balanceSolver(self.base_info)._control(qoses)
            controls.extend(_controls)
        return controls
            
class channelSwitchSolver:
    def __init__(self, target_rtt = 16, switch_state = constHead.CHANNEL0) -> None:
        self.rtt_predict = rttPredictor()
        self.target_rtt = target_rtt # ms
        self.switch_state = switch_state
        self.islog = False
        self.back_switch_threshold = 0.68
        self.last_tx_parts = [0, 0]

    def is_switch(self, qos):
        constHead.PROJ_QOS_SCHEMA.validate(qos)
        tx_parts = qos[constHead.TX_PARTS]
        if all( part == 0 for part in tx_parts) or all( part == 1 for part in tx_parts):
            return False
        actual_tx_parts = [ 1 - tx_parts[0], tx_parts[1]]
        channel_rtt = qos[constHead.CHANNEL_RTTS]
        predicted_rtt = [ channel_rtt[idx] / actual_tx_parts[idx]   for idx in range(len(actual_tx_parts)) ]
        if any( rtt < qos['target_rtt'] * self.back_switch_threshold for rtt in predicted_rtt):
            print(f"Channel RTT: {channel_rtt}, Predicted RTT: {predicted_rtt}, Target RTT: {qos['target_rtt'] * self.back_switch_threshold }")
            return True
        print(f"Predicted RTT: {predicted_rtt}, Target RTT: {qos['target_rtt'] * self.back_switch_threshold}")
        return False

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
        self.last_tx_parts = tx_parts

        if (not is_rtt_satisfy(channel_rtt[0]) and channel_rtt[1] == 0) or (not is_rtt_satisfy(channel_rtt[1]) and channel_rtt[0] == 0):
            self.switch_state = constHead.MUL_CHAN

        if all(is_rtt_satisfy(rtt) for rtt in channel_rtt) and self.switch_state == constHead.MUL_CHAN:
            try:
                return self.is_backward_switch_able()
            except Exception as e:
                print(e)

        return self

    def next_parts(self):
        return [ min(part + 0.2, 0.9) for part in self.last_tx_parts ]

class channelS2DMCSSolver:
    def __init__(self, tx_name, topo) -> None:
        self.tx_name = tx_name
        self.mcs_table = self.read_mcs_table(tx_name, topo)

    @staticmethod
    def read_mcs_table(tx_name, topo: Graph) -> None:
        mcs_table = {}
        for _tx_name, interface_infos in topo.info_graph.items():
            if _tx_name == tx_name:
                assert isinstance(interface_infos, dict)
                for key, value in interface_infos.items():
                    print(f"Key: {key}, Value: {value}")
                    try:
                        constHead.INTERFACE_INFO_SCHEMA.validate(value)
                        mcs_table[LINK_NAME_TO_TX_IF_NAME(key)] = value
                    except Exception as e:
                        print(e)
                        continue
        return mcs_table
    
    def mcs2transmission(self) -> None:
        # mcs_table 
        tx_parts = []
        mcs_values = []
        for key, value in self.mcs_table.items():
            mcs_values.append(value['MCS'])
        assert len(mcs_values) == 2
        tx_parts = [ mcs_values[1] / sum(mcs_values), mcs_values[1] / sum(mcs_values) ]
        res_tx_parts = []
        for tx_part in tx_parts:
            res_tx_parts.append( round(tx_part, 2) )
        return res_tx_parts

class channelS2DAppSolver:
    @staticmethod
    def get_tx_parts(qoses):
        tx_partss = []
        for qos in qoses:
            try:
                constHead.PROJ_QOS_SCHEMA.validate(qos)
            except Exception as e:
                continue
            tx_partss.append({'name': qos['name'], 'tx_parts': qos[constHead.TX_PARTS]})
        return tx_partss
    
    @staticmethod
    def validate_device(qoses, light):
        if light != constHead.RED_LIGHT:
            return None
        
        tx_partss = channelS2DAppSolver.get_tx_parts(qoses)
        
        for ctl in tx_partss:
            constHead.CHANNEL_CONTROL_SCHEMA.validate(ctl)
            tx_parts = ctl['tx_parts']
            if ( all(tx_parts) == 0 or all(tx_parts) == 1 ):
                return ctl['name']
        return None
    
    @staticmethod
    def next_parts(qoses, light):
        tx_partss = channelS2DAppSolver.get_tx_parts(qoses)
        stream_name = channelS2DAppSolver.validate_device(qoses, light)
        for tx_parts in tx_partss:
            if tx_parts['name'] == stream_name:
                tx_parts['tx_parts'] = [ min(part + 0.2, 1) for part in tx_parts['tx_parts'] ]
        return tx_partss
    
    @staticmethod
    def solve(last_qoses, qoses):
        def validate(last_qoses, qoses):
            assert len(last_qoses) == len(qoses)
            for idx in range(len(last_qoses)):
                constHead.PROJ_QOS_SCHEMA.validate(last_qoses[idx])
                constHead.PROJ_QOS_SCHEMA.validate(qoses[idx])
                
        def get_ctl_tx_parts(last_qoses, qoses):
            tx_partss = []; last_tx_partss = []
            for qos in qoses:
                name = qos['name']
                last_qos = [ last_qos for last_qos in last_qoses if last_qos['name'] == name ][0]
                print(f"Last QOS: {last_qos}, QOS: {qos}")
                last_tx_parts = last_qos[constHead.TX_PARTS]
                tx_parts = qos[constHead.TX_PARTS]
                if all( last_val == tx_val for last_val, tx_val in zip(last_tx_parts, tx_parts) ):
                    continue
                print(f"Last TX Parts: {last_tx_parts}, TX Parts: {tx_parts}")
                last_tx_partss.append({'name': name, 'tx_parts': last_tx_parts})
                tx_partss.append({'name': name, 'tx_parts': tx_parts})
            
            if len(tx_partss) != 1:
                raise Exception("Invalid tx_parts")
            return last_tx_partss[0], tx_partss[0]
                
        last_rtt_qoses = get_proj_qos(last_qoses)
        rtt_qoses = get_proj_qos(qoses)
        validate(last_rtt_qoses, rtt_qoses)
        
        last_qos_names  = [ qos['name'] for qos in last_rtt_qoses ]
        rtt_qoses       = order_qos(rtt_qoses, last_qos_names )
        
        print(rtt_qoses)
        last_tx_parts, tx_parts = get_ctl_tx_parts(last_rtt_qoses, rtt_qoses) 
        
        constraints = []
        obj_func = None
        for last_qos, qos in zip(last_rtt_qoses, rtt_qoses):
            predictor = rttPredictor()

            predictor.update(last_tx_parts['tx_parts'], last_qos['channel_rtts'])
            predictor.update(tx_parts['tx_parts'], qos['channel_rtts'])
            if qos['name'] == tx_parts['name']:
                obj_func = predictor.get_object()
                print([ obj_func(val) for val in np.linspace(0, 1, 10)])
                
            else:
                con1, con2 = predictor.get_constraints(qos['target_rtt']) # TODO: target rtt input
                print([ con1(val) for val in np.linspace(0, 1, 10)])
                print([ con2(val) for val in np.linspace(0, 1, 10)])
                constraints.append(con1)
                constraints.append(con2)
                
        ## Solve the optimization problem
        inequality_constraints = [ {'type': 'ineq', 'fun': con} for con in constraints]
        from scipy.optimize import minimize
        res = minimize(obj_func, np.array([0.5]), constraints=inequality_constraints , bounds = [(0,1)], tol=1e-6,method='SLSQP')
        
        if not res.success:
            print(res) 
        
        controls = []
        for qos in rtt_qoses:
            if qos['name'] == tx_parts['name']:
                controls.append({'name': qos['name'], 'tx_parts': [round(res.x[0], 2), round(res.x[0], 2)]})
            else:
                controls.append({'name': qos['name'], 'tx_parts': qos['tx_parts']})
        return controls

class thruSolver:
    @staticmethod
    def next_thru_control(qoses, name = ''):
        file_qos = get_file_qos(qoses)
        ctl_name = name
        if name == '':
            print('No name given, use the first file qos as the target')
            ctl_name = file_qos[0][constHead.NAME]
        file = get_qos_by_name(qoses, ctl_name)
        control = constHead.THRU_CONTROL_SCHEMA.validate(file)
        control[constHead.THRU_CONTROL] = int(control[constHead.THRU_CONTROL] / 2)
        return control
        
    @staticmethod
    def solve(last_qoses, qoses, name = ''):
        ## detect files 
        file_qos = get_file_qos(qoses)
        ctl_name = name
        if name == '':
            ctl_name = file_qos[0][constHead.NAME]
        ## Get target
        file    = get_qos_by_name(last_qoses, ctl_name)
        file_   = get_qos_by_name(qoses, ctl_name)
        assert file[constHead.CHANNEL] == file_[constHead.CHANNEL]
        channel_val = file[constHead.CHANNEL][0]
        print(f"Channel: {channel_val}")
        ## target proj
        projs   = get_qoss_by_channel(get_proj_qos(last_qoses), channel_val)
        projs_  = get_qoss_by_channel(get_proj_qos(qoses), channel_val)
        assert len(projs) == len(projs_)
        
        projs, projs_  = align_qos(projs, projs_)
        
        channel_rtt_idx = 0 if channel_val == constHead.CHANNEL0 else 1
        ## compute constaint
        constraint_funcs = []
        for proj, proj_ in zip(projs, projs_):
            thru_predictor = thruRTTPredictor()
            
            ## create target data
            data = {}; data.update({constHead.RTT: proj[constHead.CHANNEL_RTTS][channel_rtt_idx]}); data.update(file)
            print('last data:', data)
            thru_predictor.update(data)
            
            data = {}; data.update({constHead.RTT: proj_[constHead.CHANNEL_RTTS][channel_rtt_idx]}); data.update(file_)
            print('current data:', data)
            thru_predictor.update(data)
            
            constraint_funcs.append(thru_predictor.get_constraint(proj_))
            
        def positive_constraint(x):
            return x
        constraint_funcs.append(positive_constraint)
        inequality_constraints = [ {'type': 'ineq', 'fun': con} for con in constraint_funcs]
        
        ## find feasible point
        def obj_func(x):
            return -x
        from scipy.optimize import minimize
        res = minimize(obj_func, np.array([0.5]), constraints=inequality_constraints, tol=1e-6, method='SLSQP')
        
        control = {}
        control['name'] = ctl_name
        throttle = int(res.x[0])
        if throttle == 0:
            throttle = 1
        control[constHead.THRU_CONTROL] = throttle
        constHead.THRU_CONTROL_SCHEMA.validate(control)
        return control

class singleDirFlowTransSolver:
    def __init__(self, direction, islog = False) -> None:
        self.direction  = direction
        assert direction in [constHead.FLOW_TRANSFER_TO_CHANNEL0, constHead.FLOW_TRANSFER_TO_CHANNEL1, constHead.FLOW_STOP]
        self.islog      = islog

    def get_gap_rtt_of_target_channel(self, qoses):
        interested_rtts = []
        for qos in qoses:
            constHead.PROJ_QOS_SCHEMA.validate(qos)
            if self.direction == constHead.FLOW_TRANSFER_TO_CHANNEL0 and constHead.CHANNEL0 in qos['channels']:
                interested_rtts.append( qos['target_rtt'] - qos[constHead.CHANNEL_RTTS][0])
            elif self.direction == constHead.FLOW_TRANSFER_TO_CHANNEL1 and constHead.CHANNEL1 in qos['channels']:
                interested_rtts.append( qos['target_rtt'] - qos[constHead.CHANNEL_RTTS][1])
        return interested_rtts

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


    def thru_2b_transfered(self, qos, upperbound):
        constHead.PROJ_QOS_SCHEMA.validate(qos)

        thru            = qos[constHead.THRU]
        tx_parts        = qos[constHead.TX_PARTS]

        channel_thru    = [thru * tx for tx in tx_parts]
        channel_rtt     = qos['channel_rtts']

        if self.islog:
            print(f"Channel RTT: {channel_rtt}")
            if self.direction == constHead.FLOW_TRANSFER_TO_CHANNEL0:
                print(f"RTT red, left rtt * eta: {channel_rtt[1]}  {upperbound}")
            else:
                print(f"RTT red, left rtt * eta: {channel_rtt[0]}  {upperbound}")

        if self.direction == constHead.FLOW_TRANSFER_TO_CHANNEL0:
            return  min(channel_rtt[1], upperbound) * channel_thru[1] / channel_rtt[1]
        return      min(channel_rtt[0], upperbound) * channel_thru[0] / channel_rtt[0]

    def predict_rtt_gap_change(self, qos, eff):
        constHead.PROJ_QOS_SCHEMA.validate(qos)
        channel_rtts = qos['channel_rtts']

        if self.direction == constHead.FLOW_TRANSFER_TO_CHANNEL0:
            return channel_rtts[1] / eff
        return channel_rtts[0] / eff

    def thru_2_tx_parts(self, qos, flow_thru):
        def quantized_control(part):
            ## part should have 2 decimal places
            return round(part, 2)

        constHead.PROJ_QOS_SCHEMA.validate(qos)
        thru = qos[constHead.THRU]
        tx_parts = qos[constHead.TX_PARTS]
        transfered_part = flow_thru / thru

        if self.direction == constHead.FLOW_TRANSFER_TO_CHANNEL0:
            return [tx_parts[0] - transfered_part, tx_parts[1] - transfered_part]
        return [tx_parts[0] + transfered_part, tx_parts[1] + transfered_part]

    def solve(self, qos_list: list) -> List[dict]:
        qos_list            = get_proj_qos(qos_list)
        mul_qos_list        = get_mul_chan_qos(qos_list)
        rtt_gap             = self.get_gap_rtt_of_target_channel(qos_list)

        channel_controls    = [ constHead.CHANNEL_CONTROL_SCHEMA.validate(qos) for qos in mul_qos_list ]
        efficiencies        = np.array( [ self.compute_efficiency_index(qos) for qos in mul_qos_list ] )

        if self.islog:
            print(f"Efficiencies: {efficiencies}")
            print(f"RTT Gaps: {rtt_gap}")

        sorted_efficiencies, sorted_idx = zip(*sorted(zip(efficiencies, range(len(efficiencies))), reverse=True))

        if self.islog:
            print(f"Sorted Efficiencies: {sorted_efficiencies}")
            print(f"Sorted Index: {sorted_idx}\n")

        if self.direction == constHead.FLOW_STOP or len(efficiencies) == 0:
            return []

        min_rtt_gap         = min( rtt_gap )
        for idx, eff in enumerate( sorted_efficiencies ):
            if min_rtt_gap <= 0:
                break

            orginal_idx         = sorted_idx[idx]
            transfered_thru     = self.thru_2b_transfered( mul_qos_list[orginal_idx], min_rtt_gap * eff )
            if self.islog:
                print(f"Transfered Thru: {transfered_thru}")
                print(f"Min RTT Gap: {min_rtt_gap} {min_rtt_gap - self.predict_rtt_gap_change( mul_qos_list[orginal_idx], eff )}")

            min_rtt_gap        -= self.predict_rtt_gap_change( mul_qos_list[orginal_idx], eff )

            channel_controls[orginal_idx].update({
                "tx_parts": self.thru_2_tx_parts( mul_qos_list[orginal_idx], transfered_thru )
            })

        [ constHead.CHANNEL_CONTROL_SCHEMA.validate(control) for control in channel_controls ]
        return channel_controls
