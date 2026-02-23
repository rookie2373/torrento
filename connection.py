import socket
import threading
import queue
import struct
import time

from config import DEBUG

class ConnectionManager():
    def __init__(self):
        if DEBUG:
            print("[connection.py] ConnectionManager initialized")
        self.connections = []
        self.is_running = 0

    def connect_peer(self, peers):
        if DEBUG:
            print(f"[connection.py] Creating connection thread for peer {peers.ip}:{peers.port}")
        connection_result = ConnectionThread(peers)
        self.connections.append(connection_result)

    def start_loop(self):
        if DEBUG:
            print(f"[connection.py] Starting connection manager loop with {len(self.connections)} connections")
        self.is_running = 1
        while self.is_running:
            for connection in self.connections:
                if not connection.thread.is_alive():
                    continue
                connection.check()

    def end_loop(self):
        self.is_running = 0
        if DEBUG:
            print("[connection.py] Closing all threads")
        for connection in self.connections:
            connection.stop_thread()
            if connection.thread.is_alive():
                connection.thread.join()


class PeerConnection():
    def __init__(self, connection_thread):
        self.peer = connection_thread.peer
        self.connection_established = 0

        self.send_queue = connection_thread.send_data
        self.receive_queue = connection_thread.recv_data

        self.connection_lost = 0
        self.timeout = 0
        self.connection_failed = 0
        self.tcp_socket = None

    def menu(self):
        try:
            if DEBUG:
                print(f"[connection.py] Menu starting for peer {self.peer.ip}:{self.peer.port}")
            self.establish_tcp_connection()
        except ConnectionError:
            if DEBUG:
                print(f"[connection.py] Connection error for peer {self.peer.ip}:{self.peer.port}")
            self.connection_failed = 1

            self.tcp_socket.close()
            self.tcp_socket = None
            return

        while not self.connection_lost:
            time.sleep(1)
            self.send_message()
            self.receive_message()

        self.tcp_socket.close()
        self.tcp_socket = None

    def establish_tcp_connection(self):
        if DEBUG:
            print(f"[connection.py] Establishing TCP connection to {self.peer.ip}:{self.peer.port}")
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.settimeout(3.0)
        try:
            self.tcp_socket.connect((self.peer.ip, self.peer.port))
            if DEBUG:
                print(f"[connection.py] TCP connection established to {self.peer.ip}:{self.peer.port}")
        except OSError as e:
            if DEBUG:
                print(f"[connection.py] ERROR: TCP connection failed to {self.peer.ip}:{self.peer.port}: {str(e)}")

        self.connection_established = 1
        self.mark_connection_complete()

    def mark_connection_complete(self):
        self.peer.peer_connection_made(self)

    def add_data(self, data):
        self.send_queue.append(data)

    def send_message(self):
        while True:
            try:
                data = self.send_queue.pop()
                if data:
                    try:
                        self.tcp_socket.send(data)
                    except OSError:
                        self.connection_lost = 1
                        if DEBUG:
                            print(__name__ + ".py")
                            print("Connection lost")
                    if self.connection_lost:
                        return
            except:
                return

    def receive_message(self):
        if not self.tcp_socket:
            self.connection_lost = 1
            return

        try:
            data = self.tcp_socket.recv(4096)
        except ConnectionError:
            print("connection lost")
            self.connection_lost = 1
            return
        except socket.timeout:
            return

        else:
            if data:
                self.receive_queue.append(data)
                return
            return

    def check_connection(self):
        if self.connection_failed:
            self.connection_failed = 0
            self.handle_connection_failed()
        if self.connection_lost:
            self.connection_lost = 0
            self.handle_connection_failed()

    def handle_connection_failed(self):
        self.peer.handle_failed_connection()

    def close_connection(self):
        self.connection_lost = 1


class ConnectionThread():
    def __init__(self, peer):
        self.peer = peer
        self.recv_data = []
        self.send_data = []

        self.connection_failed = 0
        self.connection_lost = 0
        self.thread_should_stop = False

        self.main_connection = PeerConnection(self)

        self.thread = threading.Thread(target=self.main_connection.menu)
        self.thread.start()

    def check(self):
        if self.recv_data:
            self.recv_data.reverse()
            while self.recv_data:
                data = self.recv_data.pop()
                if data:
                    self.peer.handle_peer_response(data)
        if not self.thread_should_stop:
            self.main_connection.check_connection()

    def stop_thread(self):
        self.thread_should_stop = True
        self.main_connection.close_connection()


connection_manager = ConnectionManager()