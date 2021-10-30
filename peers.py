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
        resp = self.make_handshake(self.torr.meta_struct['info_hash'],CONFIG['peer_id'])
        self.send_msg(resp)

    def make_handshake(self,info_hash,peer_id):
        pstr = b'BitTorrent protocol'
        format = '!B%ds8X20s20s' % len(pstr)
        data = struct.pack(format,len(pstr),info_hash,peer_id)
        return data

    def send_msg(self,data):
        if self.con:
            self.con.add_msg(data)

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
        msg_No = None
        if msg_type == 'choke':
            msg_No=0 #fixed length no payload
        elif msg_type == 'unchoke':
            msg_No=1 #fixed length no payload
        elif msg_type == 'interested':
            msg_No=2 #fixed length no payload
        elif msg_type == 'not interested':
            msg_No = 3 #fixed length no payload
        msg = struct.pack('%d',msg_No)

        return msg



    def downloading(self):
        # check if is handshake is done or not
        if not self.connect_start:
            self.handshake()
        elif self.peer_choking:
            self.pass_msg('interested')




