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

def get_file_qos(qos_list):
    file_qos = []
    for qos in qos_list:
        try:
            constHead.FILE_QOS_SCHEMA.validate(qos)
            file_qos.append(qos)
        except:
            pass
    return file_qos

def get_qoss_by_channel(qos_list, ch):
    assert ch in [constHead.CHANNEL0, constHead.CHANNEL1], f'Invalid channel {ch}'
    ch_qoss = []
    for qos in qos_list:
        try:
            constHead.QOS_SCHEMA.validate(qos)
            if ch in qos[constHead.CHANNEL]:
                ch_qoss.append(qos)
        except:
            continue
    return ch_qoss

def get_qos_by_name(qos_list, name):
    for qos in qos_list:
        try:
            constHead.QOS_SCHEMA.validate(qos)
            if name == qos[constHead.NAME]:
                return qos
        except:
            continue
    raise ValueError(f'Invalid name {name}')

def get_mul_chan_qos(qos_list):
    mul_chan_qos = []
    for qos in qos_list:
        try:
            constHead.DOUBLE_CHANNEL_SCHEMA.validate(qos)
            mul_chan_qos.append(qos)
        except:
            pass
    return mul_chan_qos

def order_qos(qos_list, qos_names):
    assert len(qos_list) == len(qos_names)
    ordered_qos = []
    for qos_name in qos_names:
        for qos in qos_list:
            if qos['name'] == qos_name:
                ordered_qos.append(qos)
    return ordered_qos

def align_qos(last_qoses, qoses):
    assert len(last_qoses) == len(qoses)
    last_qos_names  = [ qos['name'] for qos in last_qoses ]
    aligned_qoses   = order_qos(qoses, last_qos_names )
    return last_qoses, aligned_qoses