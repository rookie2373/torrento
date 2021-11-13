# Classes for making and handling peer connections

# Import required modules
import socket
import threading
import queue
import struct
import time

# Class which creates multiple connections and keeps them active via threads
class conn_using_thread():
    def __init__(self):
        # List of active connections 
        self.connection = []
        self.running_con = 0

    # Function to create an active connection
    def conn_peer(self, peers):
        conn_res = threading_connection(peers)
        self.connection.append(conn_res)

    # Start the connection loop
    def start_loop(self):
        self.running_con = 1
        while self.running_con:
            for each_con in self.connection:
                if not each_con.thread.is_alive():
                    # print("recv from peer", each_con)
                    continue
                time.sleep(3.0)
                # if the connection of current thread is alive we call the func check on it
                each_con.check()

    # Close every active connection
    def end_loop(self):
        self.running_con = 0
        for each_con in self.connection:
            each_con.Close_connection()


# The main class for creating connection
class main_connection():
    # Constructor of the class
    def __init__(self, thread_con):
        self.peer = thread_con.peer
        # isConnected
        self.con_done = 0

        self.send = thread_con.send_data
        self.recv = thread_con.recv_data
        
        # Connection statuses
        self.connet_lost = 0
        self.timeout = 0
        self.connection_failed = 0

    # Function make a connection
    def menu(self):
        try:
            # connect using TCP
            self.Tcp_connect()
        # else --> close the connection
        except connectionfailedError:
            print("connection failed")
            self.connection_failed = 1
            self.S.close()
            self.S = None
            return

        # While connection not lost --> send and receive messages
        while not self.connet_lost:
            time.sleep(1)
            self.send_msg()
            self.recv_msg()

        # connection is lost --> close that connetion
        self.S.close() 
        self.S = None


    # Function to connect using TCP
    def Tcp_connect(self):
        # Creating a TCP socket
        self.S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # setting default timeout
        self.S.settimeout(3.0)
        # Trying to connect to peer
        try:
            self.S.connect((self.peer.ip, self.peer.port))
        except OSError:
            #self.S.close()
            raise connectionfailedError
            #self.Conn_failed_handle()

        # connection is done
        self.con_done = 1
        # Call conn_complete
        self.conn_complete()

    # Function to call peers con made handle
    def conn_complete(self):
        self.peer.con_made_handle(self)

    # Function to add data to buffer
    def add_data(self, data):
        self.send.append(data)
    
    # Funcion to send message via TCP
    def send_msg(self):
        while True:
            try:
                data = self.send.pop()
                # If data is available --> send data to socket
                if data:
                    # print("send - ip port", self.peer.ip, self.peer.port)
                    try:
                        self.S.send(data)
                    except OSError:
                        self.connet_lost = 1
                        print("Connection lost")
                    if self.connet_lost:
                        return
            except :
                    # send list is empty so return
                    return

    # Function to receive message via TCP
    def recv_msg(self):
        try:
            data = self.S.recv(4096)
        except ConnectionError:
            print("connection lost")
            self.connet_lost = 1
            return
        except socket.timeout:
            # print("timeout")
            return
        else:
            # print(print(".->",len(data)))
            if data:
                # taking the data in recv list
                self.recv.append(data)
                return
            return


    # Function to
    def connection_check(self):
        if self.connection_failed:
            self.connection_failed = 0
            # self.Conn_failed_handle()
        if self.connet_lost:
            self.connet_lost = 0
            # self.Conn_failed_handle()

    # Function to
    def Conn_failed_handle(self):
        self.peer.handle_failed_con()


# The class which fires the threads which make the connection
class threading_connection():
    def __init__(self,peer):
        self.peer = peer
        # for checking data is continously
        self.recv_data = []
        self.send_data = []        
        
        # connection status
        self.connection_failed = 0
        self.connection_lost = 0

        # connector object
        self.main_conn = main_connection(self)

        # Create thread for each peer connection and fire it
        # Function which runs is main_connection.menu()
        self.thread = threading.Thread(target=self.main_conn.menu)
        self.thread.start()

    # Function to check received data
    def check(self):
        if self.recv_data:
            self.recv_data.reverse()
            while self.recv_data:
                data = self.recv_data.pop()
                if data:
                    self.peer.Peer_resp(data)

        self.main_conn.connection_check()

    # Close the TCP connection
    def Close_connection(self):
        self.S.close()
        self.S = None

# Class for exception connectionfailedError
class connectionfailedError(Exception):
    pass

con_menu = conn_using_thread()