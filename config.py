import math
import logging

DEBUG = False

# Configure logging - least verbose by default
LOG_LEVEL = logging.DEBUG if DEBUG else logging.WARNING

logging.basicConfig(
    level=LOG_LEVEL,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

MB_FACTOR = 1048576
CONFIG = {
    'peer_id': b'QQ-0000-000000000000',
    'block_length': int(math.pow(2, 14)),
    'max_peers': 10
}