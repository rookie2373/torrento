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
        self.am_choking = 1
        self.am_interested = 0
        self.peer_choking = 1
        self.peer_interested = 0
        self.connect_failed = 0
        self.con = None
        self.connect_start = 0

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





    def handshake_resp(self,resp):
        # parsing the handshake resp according the formate as we send
        if not self.connect_start:
            self.parse_hand_resp(resp)
        else:
            print("Handshake is already done")



    def downloading(self):
        # check if is handshake is done or not
        if not self.connect_start:
            self.handshake()
        




