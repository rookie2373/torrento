from peers import Peers
from torr_download import torr_Download
from config import CONFIG
import time


class Client_Torrent():

    def __init__(self, meta_struct, con_menu):
        self.meta_struct = meta_struct
        self.con_menu = con_menu  # assigning the object of connection using thread class (from connection.py)
        self.present_peer = []
        self.peer_list = []  # peer object list
        # self.trackers = None
        self.complete = False
        self.piece_request = [[] for i in
                              self.meta_struct['info']['pieces']]  # creating the empty list for requested peer object
        self.torr_down_list = []
        self.torr_down = None
        self.conn_failed_history = []
        self.Completed_pieces = [0 for i in meta_struct['info']['pieces']]
        self.chunks = [[] for i in self.meta_struct['info']['pieces']]  # to storing the downloaded pieces
        self.rare_inx = []

    def torrent_conn(self):
        l = len(self.peer_list)
        peer_count = 0
        while (peer_count < CONFIG['max_peers'] and peer_count < len(self.peer_list)):
            self.peer_list[peer_count].make_conn()
            self.torr_down = self.torr_down_list[peer_count]
            peer_count += 1

    def make_peerlist(self, peer_dict):

        each_peer = self.check_peer(**peer_dict)  # if it is already present
        if each_peer:
            return each_peer

        peer = Peers(self, **peer_dict)  # here self is torrent obj
        torr_obj = torr_Download(peer, self)  # creating obj of torr_Download class for each peer
        self.torr_down_list.append(torr_obj)
        self.peer_list.append(peer)
        return peer

    def check_peer(self, ip, port, peer_id=None):
        for peers in (self.present_peer, self.peer_list):
            for i in peers:
                if i.ip == ip and i.port == port:  # only checking ip and port bcus peer_id may be different for same ip and port
                    return i
        return False

    def check_torr_down_obj(self, peer):
        for i in range(len(self.peer_list)):
            if self.peer_list[i] == peer:
                self.torr_down = self.torr_down_list[i]

    def peer_stopped_recovery(self):

        if self.complete:
            return
        for i in self.peer_list:
            if not i.connect_failed:
                continue

            if i in self.conn_failed_history:
                # atmost one try to connect to that peer
                continue
            self.conn_failed_history.append(i)

            while not i.con:
                try:
                    i.make_conn()
                    i.con = 1
                    print('current peer is failed : starting new peer :', i)
                except:
                    time.sleep(2)

            if i.con:
                break
        return

    def store_piece(self, piece_inx, data):
        # storing the piece into the complete list
        self.Completed_pieces[piece_inx] = data
        # the piece which is complete
        self.chunks[piece_inx] = 0

    def con_count(self):
        # to calculating the connected peers
        count = 0
        for peer in self.peer_list:
            if peer.con:
                count += 1
        return count

    def rarest_1st(self):
        # assigning  the count of each index of piece
        total_pieces = len(self.meta_struct['info']['pieces'])

        for i in range(total_pieces):
            con_ct = self.con_count()
            x = 0
            temp_count = 0

            while (x < con_ct):
                if self.peer_list[x].peer_piece_list[i]:
                    # print(self.peer_list[x].peer_piece_list)
                    temp_count += 1
                x += 1
            self.rare_inx.append((i, temp_count))

    def set_rar_inx(self, inx_tuple):
        if self.rare_inx and inx_tuple in self.rare_inx:
            self.rare_inx.remove(inx_tuple)
