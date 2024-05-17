from schema import Schema, And, Use, Optional, Or 
import util.constHead as constHead 

schema_dict = {Optional('MCS'): float}
schema_dict.update(constHead.PROJ_QOS_SCHEMA.__dict__['_schema'])
if_rtt_qos_schema = Schema(schema_dict)

schema_dict = {Optional('MCS'): float}
schema_dict.update(constHead.FILE_QOS_SCHEMA.__dict__['_schema'])
if_thru_qos_schema = Schema(schema_dict)

if_schema = Or(if_rtt_qos_schema, if_thru_qos_schema)

class senseEnv():
    def __init__(self, ignore_idx) -> None:
        self.ignore_idx = ignore_idx
        
    def calibrate(self, if_qoses):
        expected_delays = []
        for if_qos in if_qoses:
            try:
                if_schema.validate(if_qos)
            except:
                continue
            if if_qos['name'] == self.ignore_idx:
                continue
            mcs =  if_qos['MCS'] if 'MCS' in if_qos else 866.7
            expected_delay = if_qos[constHead.THRU] / mcs
            expected_delays.append(expected_delay)
        alpha = (1 / sum(expected_delays) - 1)
        return alpha
        
    def timeOfFlow(self, if_qos, calIndex):
        try:
            if_schema.validate(if_qos)
        except:
            return 0
        if if_qos['name'] == self.ignore_idx:
            return 0
        mcs =  if_qos['MCS'] if 'MCS' in if_qos else 866.7
        return if_qos[constHead.THRU] * (1 + calIndex) / mcs
    
    def timeOfFlows(self, if_qoses, calIndex):
        return [self.timeOfFlow(if_qos, calIndex) for i, if_qos in enumerate(if_qoses)]
    
    

        
        