
import struct
import requests
import bencodepy
import socket
import logging

from config import CONFIG, DEBUG

logger = logging.getLogger(__name__)

CONNECTION_ID_INITIAL = 0x41727101980
DEFAULT_TRANSACTION_ID = 5400
DEFAULT_LISTENING_PORT = 64173
DEFAULT_NUM_WANT = 10
BITS_PER_BYTE = 8
BYTES_PER_PEER_ENTRY = 6

def client_request(torrent, metainfo, announce):
    logger.info("Starting tracker request")
    if 'announce_list' in metainfo:
        announce_str = str(announce[0])
    else:
        announce_str = str(announce)

    protocol = announce_str[2:5]
    url = ''
    port = ''
    url_parsing_status = 0

    for char in announce_str:
        if char == '/' and url_parsing_status != 2:
            url_parsing_status = 1
        elif char == ':' and url_parsing_status == 1:
            url_parsing_status = 2
        elif url_parsing_status == 2 and char.isdigit():
            port += char
        elif url_parsing_status == 1:
            url += char

    logger.info(f"Tracker URL: {url}:{port}, Protocol: {protocol}")

    if protocol == 'udp':
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        host = socket.gethostbyname(url)
        port = int(port)

        connection_id = CONNECTION_ID_INITIAL
        action = 0

        transaction_id = DEFAULT_TRANSACTION_ID

        connect_request = struct.pack(">QLL", connection_id, action, transaction_id)

        sock.sendto(connect_request, (host, port))

        response1 = sock.recv(16)
        action, transaction_id, connection_id = struct.unpack(">LLQ", response1)

        if DEBUG:
            print(f"[tracker.py] UDP Connect response - action: {action}, trans_id: {transaction_id}, conn_id: {connection_id}")

        info_hash = metainfo['info_hash']
        peer_id = CONFIG['peer_id']

        listening_port = DEFAULT_LISTENING_PORT  
        uploaded = 0    
        downloaded = 0  

        left = int(metainfo['info']['length'])

        event = 2
        ip = 0
        key = 0
        num_want = DEFAULT_NUM_WANT
        action = 1

        send_data = struct.pack(">QLL20s20sQQQLLLLH", connection_id, action, transaction_id, info_hash, peer_id, downloaded, left, uploaded, event, ip, key, num_want, listening_port)

        sock.sendto(send_data, (host, port))

        response2 = sock.recv(1024)
        response_dict = {}

        action, transaction_id, interval, leechers, seeders = struct.unpack("!LLLLL", response2[:20])

        if DEBUG:
            print(f"[tracker.py] UDP Announce response - interval: {interval}s, leechers: {leechers}, seeders: {seeders}")

        handle_udp_tracker_response(torrent, response2)
        response_dict['action'] = action
        response_dict['transaction_id'] = transaction_id
        response_dict['interval'] = interval
        response_dict['leechers'] = leechers
        response_dict['seeders'] = seeders

    else:
        http_response = requests.get(announce, {
            'info_hash': metainfo['info_hash'],
            'peer_id': CONFIG['peer_id'],
            'port': 6883,  
            'uploaded': '0',  
            'downloaded': '0',  
            'left': str(metainfo['info']['length']),
        })

        handle_http_tracker_response(torrent, http_response)
    return


def construct_ip(ip_tuple):
    ip = ''
    for octet in ip_tuple:
        ip += str(octet)
        ip += '.'
    return ip[:len(ip) - 1]

def construct_port(port_tuple):
    port = ''
    for byte_val in port_tuple:
        port += str(byte_val)
    return int(port)

def decode_response(tracker_response):
    logger.debug("Decoding tracker response")
    response_dict = {}

    if b'failure reason' in tracker_response:
        error_msg = tracker_response[b'failure reason'].decode('utf-8')
        logger.error(f"Tracker error: {error_msg}")
        print(error_msg)

    response_dict['interval'] = int(tracker_response[b'interval'])

    logger.debug(f"Interval: {response_dict['interval']} seconds")

    if b'complete' in tracker_response:
        response_dict['complete'] = int(tracker_response[b'complete'])
    else:
        response_dict['complete'] = None

    logger.debug(f"Complete (seeders): {response_dict['complete']}")

    if b'incomplete' in tracker_response:
        response_dict['incomplete'] = int(tracker_response[b'incomplete'])
    else:
        response_dict['incomplete'] = None
        
    logger.debug(f"Incomplete (leechers): {response_dict['incomplete']}")
    if DEBUG:
        print("[tracker.py] Interval:", response_dict['interval'])

    peers = tracker_response[b'peers']

    if DEBUG:
        print(__name__ + ".py")
        print("Peers are:", peers)

    response_dict['peers'] = decode_peer_list(peers)

    return response_dict

def decode_peer_list(peers):
    logger.debug(f"Decoding peer list, format: {type(peers).__name__}")
    peer_list = {}
    if isinstance(peers, list):
        peer_list = decode_for_dict_model(peers)
    elif isinstance(peers, bytes):
        peer_list = decode_for_binary_model(peers)
    else:
        logger.error("Invalid peer list format")
        print('[tracker.py] Error: peer_list not formattable')
    logger.info(f"Decoded {len(peer_list)} peers")
    return peer_list

def decode_for_dict_model(list_of_peers):
    logger.debug(f"Decoding peer list in dict model format, {len(list_of_peers)} peers")
    peer_list = []
    for peer in list_of_peers:
        peer_dict = {}
        peer_dict['ip'] = peer[b'ip'].decode('utf-8')
        peer_dict['port'] = peer[b'port']
        peer_dict['peer_id'] = peer[b'peer id']
        peer_list.append(peer_dict)

    return peer_list

def decode_for_binary_model(bytes_peers):
    logger.debug(f"Decoding peer list in binary model format, {len(bytes_peers)} bytes")
    BYTES_FORMAT = '!BBBBH'
    bytes_per_peer = struct.calcsize(BYTES_FORMAT)

    if len(bytes_peers) % bytes_per_peer != 0:
        logger.error("Invalid peer list length")
        print('[tracker.py] Error: Invalid peer list length')

    peers = []
    for byte_offset in range(0, len(bytes_peers), bytes_per_peer):
        peers.append(struct.unpack_from(BYTES_FORMAT, bytes_peers, offset=byte_offset))

    list_of_peers = []
    for peer_entry in peers:
        peer_dict = {}
        peer_dict['ip'] = '%d.%d.%d.%d' % peer_entry[:4]
        peer_dict['port'] = int(peer_entry[4])
        list_of_peers.append(peer_dict)

    logger.debug(f"Decoded {len(list_of_peers)} peers from binary data")
    return list_of_peers


def handle_udp_tracker_response(torrent, response):
    response_body = response[20:]
    peer_list = []
    offset = 0

    while offset < len(response_body):
        peer_dict = {}
        ip_bytes = struct.unpack("!BBBB", response_body[offset:offset + 4])
        port_bytes = struct.unpack("!H", response_body[offset + 4:offset + 6])

        peer_dict['ip'] = construct_ip(ip_bytes)
        peer_dict['port'] = construct_port(port_bytes)

        peer_list.append(peer_dict)
        offset += 6

    if DEBUG:
        print(__name__ + ".py")
        print(peer_list)
        print()

    for peer_data in peer_list:
        if peer_data['ip'] and peer_data['port'] > 0:
            torrent.make_peer_list(peer_data)

def handle_http_tracker_response(torrent, http_response):
    tracker_response = bencodepy.decode(http_response.text.encode('latin-1'))

    if DEBUG:
        print(__name__ + ".py")
        print(tracker_response)
        print()

    response_dict = decode_response(tracker_response)
    peer_list = response_dict['peers']

    if len(peer_list) == 2:
        torrent.make_peer_list(peer_list)
        return

    for peer_data in peer_list:
        if peer_data['ip'] and peer_data['port'] > 0:
            torrent.make_peer_list(peer_data)
    return