from schema import Schema, And, Use, Optional, Or

CHANNEL0     = '5 GHz'
CHANNEL1     = '2.4 GHz'
MUL_CHAN     = 2

FLOW_TRANSFER_TO_CHANNEL0   = 'to_2.4G'
FLOW_TRANSFER_TO_CHANNEL1   = 'to_5G'
FLOW_STOP                   = 'stop'

FLOW_DIR = 'flow_dir'

RED_LIGHT       = 0
GREEN_LIGHT     = 1
YELLOW_LIGHT    = 2

################################
CHANNEL_RTTS    = 'channel_rtts'
THRU            = 'file_thru'
TX_PARTS        = 'tx_parts'
################################

CHANNEL_RTT_SCHEMA  = Schema([Or(float, int),  Or(float, int)])
TX_PARTS_SCHEMA     = Schema([And(Or(float, int), lambda n: 0 <= n <= 1), And(Or(float, int), lambda n: 0 <= n <= 1)])

# Custom function to convert string to float or int
def str_to_float_or_int(value):
    try:
        if isinstance(value, (float, int)):
            return value
        return float(value) if '.' in value else int(value)
    except ValueError:
        raise ValueError(f"Value '{value}' cannot be cast to float or int")

PROJ_QOS_SCHEMA = Schema(
    {
        "file_thru": Use(str_to_float_or_int),
        "rtt": Or(float, int),
        "target_rtt": Or(float, int),
        "tx_parts": TX_PARTS_SCHEMA,
        "channels": [Or(CHANNEL0, CHANNEL1)],
        "channel_probabilities": [Or(float, int)],
        Optional("channel_rtts"): CHANNEL_RTT_SCHEMA,
        "name": str,
    },
    ignore_extra_keys=True,
)
FILE_QOS_SCHEMA = Schema(
    {
        "file_thru": Use(str_to_float_or_int),
        "name": str,
    },
    ignore_extra_keys=True,
)
QOS_SCHEMA      = Or(PROJ_QOS_SCHEMA, FILE_QOS_SCHEMA)


DOUBLE_CHANNEL_SCHEMA = Schema(
    {
        "channels": And(
            list,
            lambda channels: all(
                channel in [CHANNEL0, CHANNEL1] for channel in channels
            ),
            lambda channels: len(channels) == 2,
        ),
        CHANNEL_RTTS: And(
            CHANNEL_RTT_SCHEMA, lambda rtts: all(rtt > 0 for rtt in rtts)
        ),
        Optional(object): object,
    }
)

CHANNEL_CONTROL_SCHEMA = Schema({
    'tx_parts'  : TX_PARTS_SCHEMA,
    'name'      : str,
}, ignore_extra_keys=True)

GB_CONTROL_SCHEMA = Schema({
    FLOW_DIR: Or(FLOW_TRANSFER_TO_CHANNEL0, FLOW_TRANSFER_TO_CHANNEL1, FLOW_STOP),
})

traffic_config_schema = Schema(Or({
    'thru'      : int,
    'link'      : str,
    'port'      : int,
    'file_type' : Or('file', 'proj'),
    'ip_addrs'  : list[str],
    'name'      : str,
    'tx_parts'  : TX_PARTS_SCHEMA,
}, None))
