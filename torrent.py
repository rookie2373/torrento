from config import CONFIG
from peers import Peers
from torr_download import torr_Download

debug = True

class Client_Torrent():

    def __init__(self,meta_struct,con_menu):
        self.meta_struct = meta_struct
        self.con_menu = con_menu
        self.present_peer =[]
        self.peer_list =[] # peer object list
        self.conn_failed_history = []
        self.complete = False
        self.torr_down = None
        # list to store Objects of torr_download
        self.torr_down_list = []
        self.piece_request = [[] for i in self.meta_struct['info']['pieces']] # creating the empty list for each piece into the one list
        self.Completed_pieces = [0 for i in meta_struct['info']['pieces']] # to store the downloaded  whole piece
        self.chunks = [[] for i in self.meta_struct['info']['pieces']] # to storing the downloaded blocks 



    def torrent_conn(self):
        l = len(self.peer_list)

        if(debug):
            print("Peer List len: ",l)
        peer_count = 0

        if(debug):
            print("Torr Down List len:",len(self.torr_down_list))

        while(peer_count<CONFIG['max_peers'] and peer_count<len(self.peer_list)):
            self.peer_list[peer_count].make_conn()
            self.torr_down = self.torr_down_list[peer_count]
            peer_count += 1


    # Function to make peerlist
    def make_peerlist(self, peer_dict):
        each_peer = self.check_peer(**peer_dict)  # if it is already present
        if each_peer:
            return each_peer

        peer = Peers(self, **peer_dict)  # here self is torrent obj
        torr_obj = torr_Download(peer, self) # creating obj of torr_Download class for each peer
        self.torr_down_list.append(torr_obj)
        self.peer_list.append(peer)
        return peer

     # if peer id is pass as para then it get assign otherwise it default value is None
    def check_peer(self,ip,port,peer_id=None):
        for peers in (self.present_peer,self.peer_list):
            for i in peers:
                if i.ip == ip and i.port == port:
                    return i
        return None
        
    def peer_stopped_recovery(self,peer):
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
    
    def check_torr_down_obj(self, peer):
        for i in range(len(self.peer_list)):
            if self.peer_list[i] == peer:
                self.torr_down = self.torr_down_list[i]

    
    def store_piece(self,piece_inx,data):
        # storing the piece into the complete list
        self.Completed_pieces[piece_inx] = data
        # the piece which is complete
        self.chunks[piece_inx] = 0
