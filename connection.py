import socket
import threading


# connecting peers using tcp


class conn_using_thread():
    def __init__(self):
        self.connection = []
        self.running_con = 0

    def conn_peer(self, peers):
        conn_res = threading_connection(peers)
        self.connection.append(conn_res)

    def start_loop(self):
        self.running_con = 1
        while self.running_con:
            for each_con in self.connection:
                if each_con.thread.is_alive():
                    each_con.check() # if the connection of current thread is alive we called check on it

    def end_loop(self):
        pass





# threaded class

class main_connection():
    def __init__(self, thread_con):
        self.peer = thread_con.peer
        self.con_done = 0
        self.send = thread_con.send_data
        self.recv = thread_con.recv_data
        self.connet_lost = 0

    def menu(self):
        self.Tcp_connect()
        # checking is connection is lost or not
        while not self.connet_lost:
            self.send_msg()
            self.recv_msg()

        self.S.close() # connection is lost we close that connetion


    def Conn_failed_handle(self):
        self.peer.handle_failed_con()

    def Tcp_connect(self):
        self.S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.S.settimeout(5.0) # setting default timeout
        try:
            self.S.connect((self.peer.ip, self.peer.port))
        except OSError:
            self.Conn_failed_handle()
        self.con_done = 1
        self.conn_complete()

    def conn_complete(self):
        self.peer.con_made_handle(self)

    def add_data(self, data):
        self.send.append(data)


    def send_msg(self):
        while True:
            try:
                data = self.send.pop()
                if data:
                    try:
                        self.S.send(data)
                    except OSError:
                        self.connet_lost = 1
                        print("Connection lost")
                    if self.connet_lost:
                        return
            except :
                    return # send list is empty so return

    def recv_msg(self):

        try:
            data = self.S.recv(4096)
        except BlockingIOError:
            return
        except ConnectionError:
            print("connection lost")
            return
        except socket.timeout:
            return

        if self.connet_lost:
            return
        else:
            if data:
                self.recv.append(data) # taking the data in recv list


class threading_connection():
    def __init__(self,peer):
        self.peer = peer
        #for checking data is continuesly
        self.recv_data = []
        self.send_data = []
        self.main_conn = main_connection(self)
        self.thread = threading.Thread(target=self.main_conn.menu)# creating thread for each peer connetion
        self.thread.start()

    def check(self):
        if self.recv_data:
            self.recv_data.reverse() # to pop starting data from list 
            while self.recv_data:
                data = self.recv_data.pop()
                if data:
                    self.peer.Peer_resp(data)






con_menu = conn_using_thread()
