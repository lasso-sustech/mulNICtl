import os, json
from util.constHead import QOS_SCHEMA

class QosLogger:
    def __init__(self, filename:str, mode:str='w'):
        abs_path = os.path.abspath(os.path.dirname(__file__))
        print(abs_path)
        
        self.filename   = filename
        self.f          = self.create_logger_file(mode = mode)
        
    def create_logger_file(self, mode = 'w'):
        if not os.path.exists(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename))
        f = open(self.filename, mode)
        if mode == 'w':
            f.write('[')
        return f

    def log_write(self, qoses):
        for idx, qos in enumerate(qoses):
            QOS_SCHEMA.validate(qos)
        self.f.write(json.dumps(qoses, indent=4, sort_keys=True, default=str))
        self.f.write(',')
        self.f.flush()
        
    def log_close(self):
        ## remove the last ','
        self.f.seek(self.f.tell() - 1, os.SEEK_SET)
        self.f.write(']')
        self.f.close()
        
    def read_log(self):
        with open(self.filename, 'r') as f:
            return json.load(f)
        