import socket
import threading

# connecting peers using tcp


class conn_using_thread():
    def __init__(self):
        self.connection =[]
        self.running_con =0

    def conn_peer(self,peers):
        conn_res = main_connection(peers)
        self.connection.append(conn_res)

# only for single connection

class main_connection():
    def __init__(self,peer):
        self.peer = peer
        self.con_done = 0
        self.send = []
        self.recv = []
        self.Tcp_connect()

    def Conn_failed_handle(self):
        self.peer.handle_failed_con()

    def Tcp_connect(self):
        self.S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.S.settimeout(3.0)
        try:
            self.S.connect((self.ip, self.port))
        except OSError:
            self.Conn_failed_handle()
        self.con_done = 1
        self.conn_complete()

    def conn_complete(self):
        self.peer.con_made_handle(self)

    def add_msg(self,data):
        self.send.append(data)
        self.send_msg()


    def send_msg(self):
        try:
            self.S.send(self.send[len(self.send)-1])
        except OSError:
            print("Connection lost")

        self.recv_msg()

    def recv_msg(self):
        
        try:
            data = self.S.recv(4096)
        except OSError:
            print("connection lost")

        if data:
            self.recv.append(data)
            self.peer.Peer_resp(data)




con_menu = conn_using_thread()
