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
        self.trackers = None
        self.complete = False
        self.torr_down = None
        # list to store Objects of torr_download
        self.torr_down_list = []
        self.piece_request = [[] for i in self.meta_struct['info']['pieces']] # creating the empty list for each piece into the one list


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
            if i.connect_failed:
                continue
            print('current peer is failed : starting new peer :',i)
            i.make_conn()
            break
