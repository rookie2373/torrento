from config import CONFIG
from peers import Peers


class Client_Torrent():

    def __init__(self,meta_struct,con_menu):
        self.meta_struct = meta_struct
        self.con_menu = con_menu
        self.present_peer =[]
        self.peer_list =[] # peer object list
        self.trackers = None
        self.complete = False


    def torrent_conn(self):
        for p in self.peer_list[CONFIG['max_peers']]:
            p.make_conn()

    def make_peerlist(self,peer_dict):
        each_peer = self.check_peer(**peer_dict) # if it is already present
        if each_peer:
            return each_peer

        peer = Peers(self,**peer_dict) # here self is torrent obj
        self.peer_list.append(peer)
        return peer

    def check_peer(self,ip,port,**kwargs):
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