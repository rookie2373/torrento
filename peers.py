import struct
import random
# import bitarray

from config import CONFIG


class Peers():
    def __init__(self, torr, ip, port, peer_id=None):
        self.ip = ip
        self.peer_id = peer_id
        self.port = port
        self.torr = torr

        # maintaining the information of each connection of remote peer
        self.choking = 1
        self.interested = 0
        self.peer_choking = 1
        self.peer_interested = 0
        self.connect_failed = 0
        self.con = None
        self.connect_start = 0
        self.peer_piece_list = []
        self.set_peer_piece_list(self.torr)
        self.request_piece = 0

        # making list of all msg_types according the there msg id as index
        self.msg_types = ['choke', 'unchoke', 'interested', 'not_interested', 'have', 'bitfield', 'request', 'piece',
                         'cancel', 'port']

    def set_peer_piece_list(self,torr):
        for i in range(len(torr.meta_struct['info']['pieces'])):
            self.peer_piece_list.append(0)

    def make_conn(self):
        self.torr.con_menu.conn_peer(self)  # here self is my peer

    def handshake(self):
        print("Sending handshake")
        resp = self.make_handshake(self.torr.meta_struct['info_hash'],CONFIG['peer_id'])
        self.send_msg(resp)

    def make_handshake(self,info_hash,peer_id):
        pstr = b'BitTorrent protocol'
        format = '!B%ds8X20s20s' % len(pstr)
        data = struct.pack(format,len(pstr),pstr,info_hash,peer_id)
        return data

    def send_msg(self,data):
        if self.con:
            self.con.add_data(data)

    def handle_failed_con(self):
        self.connect_failed = 1
        self.con = None
        self.torr.peer_stopped_recovery()

    def con_made_handle(self, con):
        self.con = con
        print("Connection made :", self.con)
        self.downloading()

    def pass_msg(self,msg_type):
        msg = self.make_msg(msg_type)
        self.send_msg(msg)
    
    def make_msg(self,msg_type):
        #all remaining msg is of the type <length prefix><message ID><payload>
        msg_No = None  # massage ID is single byte decimal
        payload = b''# payload is massage dependent
        if msg_type == 'choke':
            msg_No=0 #fixed length no payload
        elif msg_type == 'unchoke':
            msg_No=1 #fixed length no payload
        elif msg_type == 'interested':
            msg_No=2 #fixed length no payload
        elif msg_type == 'not interested':
            msg_No = 3 #fixed length no payload
        elif msg_type == 'have':
            msg_No = 4  # fixed length
        elif msg_type == 'bitfield':
            msg_No = 5  # fixed length

        # length prefix is four byte big-endian value
        # but observe that it is  0001 when payload is empty but changes when payload length is not empty
        length_prefix = len(payload)+1
        format  = '!lB%ds' %len(payload) # B->unsigned char , l -> long , s-> char
        msg = struct.pack(format,length_prefix,msg_No,payload)

        return msg
    
    def parse_hand_resp(self,data):
        # check it is in correct format  or not
        pstrlen = int(data[0])
        remaining_data = data[1:49 + pstrlen]
        format = '!%ds8x20s20s' % pstrlen
        res = struct.unpack(format,remaining_data)
        print(res)
        dec_dict = {}
        dec_dict['pstr'] = res[0].decode('utf')
        dec_dict['info_hash'] = res[1]
        dec_dict['peed_id'] = res[2]

        if dec_dict['pstr'] == 'BitTorrent protocol':
            self.connect_start = 1 # handshake resp is correct so connction with peer is established
            print("recv handshake")
           # so handshake is ok now we can run downloading 
            self.downloading()
            
    
    # not cover this case yet
    def keep_alive_resp(self):
        pass


    def parse_msg_resp(self,msg):

        self.msg_dict = {}  # dict to store
        # extract length prefix
        length_prefix = struct.unpack('!L', msg[:4])[0] # taking first four byte from resp tuple
        self.msg_dict['length_prefix'] = length_prefix

        if length_prefix == 0:
            # keep alive massage
            self.keep_alive_resp()


        data = msg[4:4+length_prefix]
        msg_no = int(data[0])
        payload = data[1:]
        self.msg_dict['msg_no'] = msg_no
        self.msg_dict['payload'] = payload
        print(self.msg_dict)
        self.set_peer_status(msg_dict,msg_type)
    
    
    def set_peer_status(self,msg_dict,msg_type):
        # checking msg resp
        if msg_type == 'choke' :
            self.peer_choking =1
        elif msg_type == 'unchoke':
            self.peer_choking = 0
        elif msg_type == 'interested':
            self.peer_interested = 1
        elif  msg_type == 'not_interested':
            self.peer_interested = 0
        elif msg_type == 'have':
            (indx,) = struct.unpack('!L',msg_dict['payload'])# taking the index of the pieces the peers have
            self.peer_piece_list[indx] = 1 # setting the index of pieces that peer have

        elif msg_type == 'bitfield':
            payload = msg_dict['payload'] #  The payload is a bitfield representing the pieces that have been successfully downloaded
            res = bin(int.from_bytes(payload, byteorder=sys.byteorder)) # converting bytes to binary
            self.peer_piece_list = [int(res[i]) for i in range(2,len(self.torr.meta_struct['info']['pieces'])+2)] # here 1 is  indicates the pieces the peer has
        self.downloading()




    def Peer_resp(self,resp):
        # parsing the handshake resp according the formate as we send
        if not self.connect_start:
            self.parse_hand_resp(resp)
        else:
            # peers is already done handshake not receiving respense
            self.parse_msg_resp(resp)



    def downloading(self):
        # check if is handshake is done or not
        if not self.connect_start:
            self.handshake()
        elif self.choking:
            self.pass_msg('interested')
