import socket
import threading
# connecting peers using tcp




class conn_using_thread():
    def __init__(self):
        self.connection =[]
        self.running_con =[]

    def conn_peer(self,peers):
        conn_res = main_connection(peers)
        self.connection.append(conn_res)

# only for single connection

class main_connection():
    def __init__(self,peer):
        self.peer = peer
        self.Tcp_connect()
        self.con_done = 0
        self.msgs = []

    def Conn_failed_handle(self):
        self.peer.handle_failed_con()

    def Tcp_connect(self):
        self.S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.S.settimeout(4.0)
        try:
            self.S.connect((self.ip, self.port))
        except OSError:
            self.Conn_failed_handle()
        self.con_done = 1
        self.conn_complete()

    def conn_complete(self):
        self.peer.con_made_handle(self)

    def add_msg(self,data):
        self.msgs.append(data)





con_menu = conn_using_thread()