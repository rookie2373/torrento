import struct
import random
import sys

from config import CONFIG


class Peers():
    def __init__(self, torr, ip, port, peer_id=None):
        self.ip = ip
        self.peer_id = peer_id
        self.port = port
        self.torr = torr


        # maintaining the information of each connection of remote peer
        #intial assignment.
        self.choking = 1
        self.interested = 0
        self.peer_choking = 1
        self.peer_interested = 0
        self.connect_failed = 0
        self.con = None
        self.connect_start = 0
        self.peer_piece_list = []
        self.pieces_length = len(torr.meta_struct['info']['pieces'])
        self.set_peer_piece_list()
        self.request_piece = 0
        self.buffer = b'' # concanate the data if it comes in pieces
        self.starting_point = 0

        # making list of all msg_types according the there msg id as index
        self.msg_types = ['choke', 'unchoke', 'interested', 'not_interested', 'have', 'bitfield', 'request', 'piece',
                         'cancel', 'port']
                         

    def set_peer_piece_list(self):
        for i in range(self.pieces_length):
            self.peer_piece_list.append(0)

    def make_conn(self):
        self.torr.con_menu.conn_peer(self)  # here self is my peer


    def handshake(self):
        print("Sending handshake")
        resp = self.make_handshake(self.torr.meta_struct['info_hash'], CONFIG['peer_id'])
        self.send_msg(resp)

    def make_handshake(self, info_hash, peer_id):
        pstr = b'BitTorrent protocol'  # this is identity that will check that will check after handshake recv
        format = '!B%ds8x20s20s' % len(pstr)  # %d -> len(pstr) # !-> big endian
        data = struct.pack(format, len(pstr), pstr, info_hash, peer_id)
        return data

    def send_msg(self, data):
        if self.con:
            self.con.add_data(data)

    def handle_failed_con(self):
        self.connect_failed = 1
        self.con = None
        self.torr.peer_stopped_recovery(self)

    def con_made_handle(self, con):
        self.con = con
        print("Connection made :", self.con)
        self.downloading()

    def pass_msg(self, **arguments):
        msg = self.make_msg(**arguments)
        #print("send_msg",msg)
        self.send_msg(msg)

    def make_msg(self, **arguments): # here arg is dictionary

        if len(arguments) == 1 :
            msg_type = arguments['msg_type']
        else:
            msg_type = arguments['msg_type']
            piece_inx = arguments['piece_inx']
            block_length = arguments['block_length']


        # all remaining msg is of the type <length prefix><message ID><payload>
        msg_No = None  # massage ID is single byte decimal
        payload = b''  # payload is massage dependent
        if msg_type == 'choke':
            msg_No = 0  # fixed length no payload
        elif msg_type == 'unchoke':
            msg_No = 1  # fixed length no payload
        elif msg_type == 'interested':
            msg_No = 2  # fixed length no payload
        elif msg_type == 'not interested':
            msg_No = 3  # fixed length no payload
        elif msg_type == 'have':
            msg_No = 4  # fixed length
        elif msg_type == 'bitfield':
            msg_No = 5  # fixed length
        elif msg_type == 'request':
            msg_No = 6
            payload = struct.pack('!LLL',piece_inx,self.starting_point,block_length)

        # length prefix is four byte big-endian value
        # but observe that it is  0001 when payload is empty but changes when payload length is not empty
        length_prefix = len(payload) + 1
        format = '!lB%ds' % len(payload)  # B->unsigned char , l -> long , s-> char
        msg = struct.pack(format, length_prefix, msg_No, payload)

        return msg

    def parse_hand_resp(self, data):
        # check it is in correct format  or not
        pstrlen = int(data[0]) # 19
        remaining_data = data[1:49 + pstrlen] # 1->68 byte of data
        extra_data = 1 + len(remaining_data) # this length of extra data which is comes with handshake
        format = '!%ds8x20s20s' % pstrlen
        res = struct.unpack(format, remaining_data)

        dec_dict = {}
        dec_dict['pstr'] = res[0].decode('utf')
        dec_dict['info_hash'] = res[1]
        dec_dict['peed_id'] = res[2]

        if dec_dict['pstr'] == 'BitTorrent protocol':
            self.connect_start = 1  # handshake resp is correct so connction with peer is established
            print("recv handshake")
            # so handshake is ok
            self.downloading()
            return extra_data




    def parse_msg_resp(self, msg):

        msg_dict = {}  # dict to store
        # extract length prefix
        totol_bytes = 0
        # invalid resp
        if len(msg) < 4:
            return 0
        length_prefix = struct.unpack('!L', msg[:4])[0]  # taking first four byte from first tuple
        msg_dict['length_prefix'] = length_prefix
        totol_bytes += 4 # four byte length prefix

        if length_prefix == 0:
            # keep alive massage
            return totol_bytes

        # if the data that comes is not complete and its some portion is come then we just return and add that data into the buffer
        if totol_bytes + length_prefix > len(msg):
            return 0

        data = msg[totol_bytes:totol_bytes + length_prefix] # from fourth byte to the length of prefix has msg id and payload
        totol_bytes += length_prefix
        msg_no = int(data[0])
        payload = data[1:]
        msg_dict['msg_no'] = msg_no
        msg_dict['payload'] = payload
        msg_type = self.msg_types[msg_no]
        print("Peer's massage :", msg_no, msg_type, payload)
        self.set_peer_status(msg_dict,msg_type)
        return totol_bytes


    def Peer_resp(self, resp):
        # parsing the handshake resp according the formate as we send
        data = self.buffer + resp # if there remaining data which is of previous resp then we concanate that new data with the older one
        res = 0
        while data:
            if not self.connect_start:
                  res = self.parse_hand_resp(data)
            else:
                 # peers is already done handshake
                 res = self.parse_msg_resp(data)
            if res == 0:
                break
            data = data[res:] # if resp from peer is correct then this data become zero and that means buffer becomes zero
        self.buffer = data


    def downloading(self):
        # check if is handshake is done or not
        if not self.connect_start:
            self.handshake()
        elif self.peer_choking:
            print("send interested")

            self.pass_msg(msg_type = 'interested') # try to send the msg to peer that we are interested

        elif self.request_piece ==1 :
            # wait for piece to download
            pass
        else:
            # request new piece as peer unchock the client that is we
            piece_inx = self.new_piece()
            self.request_piece = piece_inx
            self.torr.piece_request[piece_inx].append(self)# here we appending object of peers so that each peer can request new index
            self.request_Block(piece_inx) # as piece length is so large that we cannot request whole piece at once
            # hence we requesting the piece in chunks we called as block

    def request_Block(self,p_indx):
        #len_piece = self.torr.meta_struct['info']['piece_length']
        
        self.pass_msg( msg_type = 'request',piece_inx = p_indx, block_length = CONFIG['block_length'])



    def new_piece(self):
               for piece_inx in range(self.pieces_length):
            # here we are checking that is current peer has the piece or not and also if that piece is already requested by another peer then we go  for next piece
                if (self.peer_piece_list[piece_inx] and not self.torr.piece_request[piece_inx]):
                    return piece_inx

    def set_peer_status(self, msg_dict, msg_type):
        # checking msg resp
        if msg_type == 'choke':
            self.peer_choking = 1
        elif msg_type == 'unchoke':
            self.peer_choking = 0
            self.downloading()  # as peer unchock we go to the downloading
        elif msg_type == 'interested':
            self.peer_interested = 1
        elif msg_type == 'not_interested':
            self.peer_interested = 0
        elif msg_type == 'have':
            (indx,) = struct.unpack('!L', msg_dict['payload'])  # taking the index of the pieces the peers have
            self.peer_piece_list[indx] = 1  # setting the index of pieces that peer have

        elif msg_type == 'bitfield':
            payload = msg_dict[
                'payload']  # The payload is a bitfield representing the pieces that have been successfully downloaded
            res = bin(int.from_bytes(payload, byteorder=sys.byteorder))  # converting bytes to binary
            self.peer_piece_list = [int(res[i]) for i in
                                    range(2, self.pieces_length + 2)]  # here 1 is  indicates the pieces the peer has
        elif msg_type == 'piece':
            starting_tuple = struct.unpack('LL', msg_dict['payload'][:8]) # taking first two byte
            piece_inx = starting_tuple[0]
            block_start = starting_tuple[1]
            self.starting_point +=  CONFIG['block_length'] # increamenting the starting point
            payload = msg_dict['payload'][8:]
            self.torr.torr_down.check_block(piece_inx, block_start, payload)
        elif msg_type =='port':
            return



