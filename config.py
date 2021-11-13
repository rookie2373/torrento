# Client Configuration file

import math
# "global"

CONFIG = {
    'peer_id': b'QQ-0000-000000000000', # unique id for client
    'block_length': int(math.pow(2,14)), # portion of data that a client request from the peer
    'max_peers': 10 # numwant
}