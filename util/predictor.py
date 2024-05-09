import numpy as np

from util.constHead import TX_PARTS_SCHEMA, CHANNEL_RTT_SCHEMA

class predictor():
    def __init__(self, len_max = 3) -> None:
        self.his_y_vals = []
        self.his_x_vals = []
        self.len_max = len_max
        
    def predict(self, x_val):
        assert len(self.his_x_vals) == len(self.his_y_vals)
        assert len(self.his_x_vals) > 1
        
        if len(self.his_x_vals) >= 3:
            ## order 2 fit
            z = np.polyfit(self.his_x_vals, self.his_y_vals, 2)
            p = np.poly1d(z)
            return p(x_val)
        
        ## order 1 fit
        z = np.polyfit(self.his_x_vals, self.his_y_vals, 1)
        print(z)
        p = np.poly1d(z)
        return p(x_val)
    
    def update(self, x_val, y_val):
        self.his_x_vals.append(x_val)
        self.his_y_vals.append(y_val)
        if len(self.his_x_vals) > self.len_max:
            self.his_x_vals.pop(0)
            self.his_y_vals.pop(0)
    
class rttPredictor():
    def __init__(self) -> None:
        self.channel_5g = predictor()
        self.channel_2g = predictor()
        
    def predict(self, tx_parts):
        TX_PARTS_SCHEMA.validate(tx_parts)
        return self.channel_5g.predict(tx_parts[0]), self.channel_2g.predict(tx_parts[1])
    
    def update(self, tx_parts, channel_rtt):
        TX_PARTS_SCHEMA.validate(tx_parts)
        CHANNEL_RTT_SCHEMA.validate(channel_rtt)
        
        self.channel_5g.update(tx_parts[0], channel_rtt[0])
        self.channel_2g.update(tx_parts[1], channel_rtt[1])
        return self