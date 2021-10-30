# Script to send request to tracker and record the response

# Import required modules
import struct
import requests
import bencodepy

# Configuration file
from config import CONFIG

# For debugging
debug = False

# Connecting to tracker

# Function to send announce request to the tracker
def clientRequest(metaInfo):
    announce = metaInfo["announce"]
    response = requests.get(announce, {
        'info_hash':metaInfo['info_hash'],
        'peer_id': CONFIG['peer_id'],
        'port': 6881,  # range (6881,6889)
        'uploaded': '0',  # total amount of upload
        'downloaded': '0',  # total amount of downloud
        'left': str(metaInfo['info']['length']),
        # 'numwant': CONFIG['max_peers']
    })

    # if(debug):
    #     print(response,response.text)

    trackerResponse(metaInfo, response)

# Function to record tracker's response
def trackerResponse(torrent, http_resp):
    # The tracker responds with "text/plain" document 
    # consisting of a bencoded dictionary
    trackResp = bencodepy.decode(http_resp.text.encode('latin-1'))

    if(debug):
        print(trackResp)

    # Constructing the response in form of dictionary
    respDict = decodeResponse(trackResp)
    peer_list = respDict['peers']

    for peer_d in peer_list:
        if peer_d['ip'] and peer_d['port']>0:
            torrent.make_peerlist(peer_d)
            

# Function to construct the response dictionary
def decodeResponse(trackResp):
    respDict = {}
    # checking if there is failure in resp
    if b'failure reason' in trackResp:
        print(trackResp[b'failure reason'].decode('utf-8'))

    # interval that the client should wait before 
    # sending the next request to the tracker
    respDict['interval'] = int(trackResp[b'interval'])

    if(debug):
        print(respDict['interval'])

    # number of peers i.e  seeders (integer)
    if b'complete' in trackResp:
        respDict['complete'] = int(trackResp[b'complete'])
    else:
        respDict['complete'] = None
    
    if(debug):
        print(respDict['complete'])

    # numbers of non seeder peers
    if b'incomplete' in trackResp:
        respDict['incomplete'] = int(trackResp[b'incomplete'])
    else:
        respDict['complete'] = None
    
    if(debug):
        print(respDict['incomplete'])

    # A string tha the client should send back to its next announcement
    if b'tracker_id' in trackResp:
        respDict['tracker_id'] = int(trackResp[b'tracker_id'])
    else:
        respDict['tracker_id'] = None
    
    if(debug):
        print(respDict['tracker_id'])

    # The peers (contain ip address and port no.)
    peers = trackResp[b'peers']

    if(debug):
        print("Peers are:",peers)

    # Appending the peer list
    respDict['peers'] = decodePeerList(peers)

    return respDict

# Function to decode peer list
def decodePeerList(peers):
    peerList = {}
    # checking if peer list uses dict model or binary model 
    # and decoding them accordingly
    if isinstance(peers, list):
        peerList = decode_for_dict_model(peers)
    elif isinstance(peers, bytes):
        peerList = decode_for_binary_model(peers)
    else:
        print('Error : Not formatable ')
    return peerList

# Function to decode peer list for dictionary model
def decode_for_dict_model(list_peers):
     peer_list = []
    for peer in list_peers:
        peer_dict = {}
        peer_dict['ip'] = peer[b'ip'].decode('utf-8')
        peer_dict['port'] = peer[b'port']
        peer_dict['peer_id'] = peer[b'peer id']
        peer_list.append(peer_dict)

    return peer_list

# Function to decode peer list for binary model
def decode_for_binary_model(bytes_peers):
    no_of_bytes = '!BBBBH'
    byte_size = struct.calcsize(no_of_bytes)

    if(debug):
        print(byte_size)
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
