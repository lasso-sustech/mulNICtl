from schema import Schema, And, Use, Optional, Or

CHANNEL_RTT_SCHEMA = Schema([Or(float, int),  Or(float, int)])
TX_PARTS_SCHEMA = Schema([And(Or(float, int), lambda n: 0 <= n <= 1), And(Or(float, int), lambda n: 0 <= n <= 1)])

CHANNEL1     = [True, False]
CHANNEL2     = [False, True]
MUL_CHAN     = [True, True]