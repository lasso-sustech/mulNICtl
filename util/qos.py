import util.constHead as constHead
from util.trans_graph import Graph
from util.stream import stream

def get_qoss(graph: Graph, res, rtts):
    proj_keys = []
    thru_keys = []
    
    stream_list = []
    for device_name, links in graph.graph.items():
        for link_name, streams in links.items():
            for stream_name, stream_handle in streams.items():
                assert isinstance(stream_handle, stream)
                if stream_handle.calc_rtt is True:
                    proj_keys.append(stream_name)
                thru_keys.append(stream_name)
                stream_list.append(stream_handle)
            
    qoses = []
    for thru_key in thru_keys:
        qos = {}
        thru_idx = thru_keys.index(thru_key)
        qos.update(res[thru_idx])
        qos.update(stream_list[thru_idx].to_dict())
        if thru_key in proj_keys:
            proj_key = thru_key
            rtt_idx  = proj_keys.index(proj_key)
            qos.update(rtts[rtt_idx].to_dict())
        qoses.append(constHead.QOS_SCHEMA.validate(qos))
    return qoses

def get_proj_qos(qos_list):
    proj_qos = []
    for qos in qos_list:
        try:
            constHead.PROJ_QOS_SCHEMA.validate(qos)
            proj_qos.append(qos)
        except:
            pass
    return proj_qos

def get_mul_chan_qos(qos_list):
    mul_chan_qos = []
    for qos in qos_list:
        try:
            constHead.DOUBLE_CHANNEL_SCHEMA.validate(qos)
            mul_chan_qos.append(qos)
        except:
            pass
    return mul_chan_qos