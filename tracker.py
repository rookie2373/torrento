# Script to send request to tracker and record the response

# Import required modules
import struct
import requests
import bencodepy
import socket
# Configuration file
from config import CONFIG

# For debugging
debug = False

# Connecting to tracker

# Function to send announce request to the tracker

# sending the anncounce request using http get request and udp
def client_request(torrent, metainfo, announce):
    str_ann = str(announce)
    protocol = str_ann[2:5]
    url = ''
    flag = 0
    port = '' # to extract the port from the announce
    for x in str_ann:
        if x == '/' and flag != 2:
            flag = 1
        elif x == ':' and flag==1:
            flag = 2
        elif flag == 2 and x.isdigit():
            port += x
        elif flag == 1:
            url += x


    if protocol == 'udp':

        S = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        host = socket.gethostbyname(url)
        port = int(port) # extracted port
        connection_id = 0x41727101980
        action =0
        transaction_id = 5400 # random
        connect_request = struct.pack(">QLL",connection_id,action,transaction_id)
        S.sendto(connect_request,(host,port))
        resp1 = S.recv(16)
        action, transaction_Id, connection_id = struct.unpack(">LLQ",resp1)
        info_hash= metainfo['info_hash']
        peer_id =CONFIG['peer_id']
        port_p =6883  # range (6881,6889)
        uploaded=0  # total amount of upload
        downloaded= 0  # total amount of downloud
        left =int(metainfo['info']['length'])
        event = 2
        ip = 0
        key = 0
        num_want = 10
        action = 1
        send_data = struct.pack(">QLL20s20sQQQLLLLH", connection_id, action,transaction_Id,info_hash, peer_id, downloaded,left,uploaded,event,ip,key,num_want,port_p)
        S.sendto(send_data, (host, port))
        resp2 = S.recv(1024)
        resp_dict = {}
        action, transaction_id, intervel, leechers, seeders = struct.unpack("!LLLLL", resp2[:20])
        #print(action,transaction_id,intervel,leechers,seeders)
        udp_trackers_resp(torrent,resp2)
        resp_dict['action'] = action
        resp_dict['transaction_id'] = transaction_id
        resp_dict['interval'] = intervel
        resp_dict['leechers'] = leechers
        resp_dict['seeders'] = seeders

    else:
        resp = requests.get(announce, {
            'info_hash': metainfo['info_hash'],
            'peer_id': CONFIG['peer_id'],
            'port': 6883,  # range (6881,6889)
            'uploaded': '0',  # total amount of upload
            'downloaded': '0',  # total amount of downloud
            'left': str(metainfo['info']['length']),
        })
        trackers_response(torrent, resp)
    return


def create_ip(ip_tuple):
    s=''
    for i in ip_tuple:
        s+=str(i)
        s+='.'
    return s[:len(s)-1]

def create_port(port_tuple):
    s=''
    for i in port_tuple:
        s+=str(i)
    return int(s)

def udp_trackers_resp(torrent,resp_):
    resp = resp_[20:]
    peer_list = []
    i = 0
    while i < len(resp):
        peer_dict ={}
        _ip = struct.unpack("!BBBB",resp[i:i+4])
        _port = struct.unpack("!H",resp[i+4:i+6])
        peer_dict['ip'] = create_ip(_ip)
        peer_dict['port'] = create_port(_port)
        peer_list.append(peer_dict)
        i += 6


    for peer_d in peer_list:

        if peer_d['ip'] and peer_d['port'] > 0:
            torrent.make_peerlist(peer_d)



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

    # for single peer 
    if len(peer_list) ==2:  
        torrent.make_peerlist(peer_list)
        return
    # for multiple peer
    for peer_d in peer_list:
        if peer_d['ip'] and peer_d['port']>0:
            torrent.make_peerlist(peer_d)
    return

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
    list_peers = []
    # besically peer has 4 byte ip add and 2 byte of port number
    for k in peers:
        peer_dict = {}
        peer_dict['ip'] = '%d.%d.%d.%d' % k[:4]
        peer_dict['port'] = int(k[4])
        list_peers.append(peer_dict)

    print(list_peers)
    return list_peers
