import struct
import requests
import bencodepy
import logging

from config import CONFIG

log = logging.getLogger(__name__)  # detecting the erroe in modulw which are imported


# connecting to trackers

# sending the anncounce request using http get request
def client_request(torrent, announce):
    resp = requests.get(announce, {
        'info_hash':torrent['info_hash'],
        'peer_id': CONFIG['peer_id'],
        'port': 6881,  # range (6881,6889)
        'uploaded': '0',  # total amount of upload
        'downloaded': '0',  # total amount of downloud
        'left': str(torrent['info']['length']),
        # 'numwant': CONFIG['maxx_peers']
    })

    trackers_response(torrent, resp)


def trackers_response(torrent, http_resp):
    # The tracker responds with "text/plain" document consisting of a bencoded dictionary

    track_resp = bencodepy.decode(http_resp.text.encode('latin-1'))
    resp_dict = decode_each_resp(track_resp)
    print(resp_dict['peers'])

    for peer_dict in resp_dict['peers']:
        # if peers ip and port is correct then add this peer to torrent

        """
        if peer_dict['ip'] and peer_dict['port'] > 0:
            print(peer_dict)
            #torrent.add_peer(peer_dict)
            """

def decode_each_resp(track_resp):
    resp_dict = {}
    # checking if there is failure in resp also there warning massage but its optional
    if b'failure reason' in track_resp:
        print(track_resp[b'failure reason'].decode('utf-8'))

    # interval such that client should wait before sending the next request to the tracker
    resp_dict['interval'] = int(track_resp[b'interval'])

    # number of peers i.e  seeders (integer)
    if b'complete' in track_resp:
        resp_dict['complete'] = int(track_resp[b'complete'])
    else:
        resp_dict['complete'] = None

    # numbers of non seeder peers
    if b'incomplete' in track_resp:
        resp_dict['incomplete'] = int(track_resp[b'incomplete'])
    else:
        resp_dict['complete'] = None

    # a string tha the client should send back to its next announcement
    if b'tracker_id' in track_resp:
        resp_dict['tracker_id'] = int(track_resp[b'tracker_id'])
    else:
        resp_dict['complete'] = None

    peers = track_resp[b'peers']

    # checking if peer list the use dict model for decoding and for binary use binary model of decode
    if isinstance(peers, list):
        resp_dict['peers'] = decode_for_dict_model(peers)
    elif isinstance(peers, bytes):
        resp_dict['peers'] = decode_for_binary_model(peers)
    else:
        print('Error : Not formatable ')
    return resp_dict


def decode_for_dict_model(list_peers):
    peer_dict = {}
    for peer in list_peers:
        peer_dict['ip'] = peer[b'ip'].decode('utf-8')
        peer_dict['port'] = peer[b'port']
        peer_dict['peer_id'] = peer[b'peer_id']

    return peer_dict


def decode_for_binary_model(bytes_peers):
    no_of_bytes = '!BBBBH'
    byte_size = struct.calcsize(no_of_bytes)
    # checking the resp binary model contain 6 bytes or not
    if len(bytes_peers) % byte_size != 0:
        print('Error: invalid length')
    peers = []
    # extracting the peers
    for i in range(0, len(bytes_peers), byte_size):
        peers.append(struct.unpack_from(no_of_bytes, bytes_peers, offset=i))
    dict_peers = {}
    # besically peer has 4 byte ip add and 2 byte of port number
    for k in peers:
        dict_peers['ip'] = '%d.%d.%d.%d' % k[:4]
        dict_peers['port'] = int(k[4])

    return dict_peers
