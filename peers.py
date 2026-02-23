
import struct
import random
import sys

from config import CONFIG, DEBUG


class Peers():
    def __init__(self, torrent, ip, port, peer_id=None):
        if DEBUG:
            print(f"[peers.py] Initializing Peers object for {ip}:{port}")
        self.ip = ip
        self.port = port
        self.torrent = torrent
        self.peer_id = peer_id

        self.choking = 1
        self.interested = 0
        self.peer_choking = 1
        self.peer_interested = 0

        self.connection_failed = 0
        self.connection_start = 0

        self.connection = None

        self.peer_piece_list = []
        self.pieces = len(torrent.torrent_metadata['info']['pieces'])

        self.set_peer_piece_list()
        self.target_piece_index = None

        self.buffer = b''
        self.starting_point = 0

        self.msg_types = ['choke', 'unchoke', 'interested', 'not_interested', 'have', 'bitfield', 'request', 'piece',
                          'cancel', 'port']

    def set_peer_piece_list(self):
        for piece_index in range(self.pieces):
            self.peer_piece_list.append(0)

    def make_connection(self):
        if DEBUG:
            print(f"[peers.py] Making connection to {self.ip}:{self.port}")
        self.torrent.connection_manager.connect_peer(self)

    def handshake(self):
        if DEBUG:
            print(f"[peers.py] Performing handshake with {self.ip}:{self.port}")
        if DEBUG:
            print(__name__ + ".py")
            print("Sending handshake")
        response = self.make_handshake(
            self.torrent.torrent_metadata['info_hash'], CONFIG['peer_id'])
        self.send_message(response)

    def make_handshake(self, info_hash, peer_id):
        protocol_string = b'BitTorrent protocol'
        protocol_format = '!B%ds8x20s20s' % len(protocol_string)
        data = struct.pack(protocol_format, len(protocol_string), protocol_string, info_hash, peer_id)
        return data

    def send_message(self, data):
        if self.connection:
            self.connection.add_data(data)

    def handle_failed_connection(self):
        if DEBUG:
            print(f"[peers.py] Connection failed with peer {self.ip}:{self.port}")
        self.connection_failed = 1
        self.connection = None
        self.torrent.peer_stopped_recovery()

    def peer_connection_made(self, connection):
        self.connection = connection
        if DEBUG:
            print(f"[peers.py] Peer connection established with {self.ip}:{self.port}")
        self.downloading()

    def pass_message(self, **arguments):
        message = self.make_message(**arguments)
        self.send_message(message)

    def make_message(self, **arguments):  
        if len(arguments) == 1:
            msg_type = arguments['msg_type']
        else:
            msg_type = arguments['msg_type']
            piece_index = arguments['piece_index']
            block_length = arguments['block_length']
            starting_point = arguments['starting_point']

        msg_number = None  

        payload = b''  

        if msg_type == 'choke':
            msg_number = 0  
        elif msg_type == 'unchoke':
            msg_number = 1  
        elif msg_type == 'interested':
            msg_number = 2  
        elif msg_type == 'not interested':
            msg_number = 3  
        elif msg_type == 'have':
            msg_number = 4  
        elif msg_type == 'bitfield':
            msg_number = 5  
        elif msg_type == 'request':
            msg_number = 6

            if DEBUG:
                print(f"[peers.py] Sending request for piece {piece_index}, offset {starting_point}, length {block_length}")

            payload = struct.pack(
                '!LLL', piece_index, starting_point, block_length)

        length_prefix = len(payload) + 1

        msg_format = '!lB%ds' % len(payload)
        message = struct.pack(msg_format, length_prefix, msg_number, payload)

        return message

    def parse_handshake_response(self, data):
        if DEBUG:
            print(f"[peers.py] Parsing handshake response from {self.ip}:{self.port}")
        protocol_string_length = int(data[0])
        remaining_data = data[1:49 + protocol_string_length]

        extra_data = 1 + len(remaining_data)

        handshake_format = '!%ds8x20s20s' % protocol_string_length
        response = struct.unpack(handshake_format, remaining_data)

        decoded_dict = {}
        decoded_dict['pstr'] = response[0].decode('utf')
        decoded_dict['info_hash'] = response[1]
        decoded_dict['peer_id'] = response[2]

        if decoded_dict['pstr'] == 'BitTorrent protocol':
            self.connection_start = 1
            if DEBUG:
                print(f"[peers.py] Handshake successful with {self.ip}:{self.port}")
            self.downloading()
            return extra_data

    def parse_message_response(self, message):
        msg_dict = {}
        total_bytes = 0

        if len(message) < 4:
            return 0

        length_prefix = struct.unpack('!L', message[:4])[0]

        msg_dict['length_prefix'] = length_prefix
        total_bytes += 4  

        if length_prefix == 0:
            return total_bytes

        if total_bytes + length_prefix > len(message):
            return 0

        data = message[total_bytes:total_bytes + length_prefix]
        total_bytes += length_prefix

        msg_number = int(data[0])
        payload = data[1:]

        msg_dict['msg_number'] = msg_number
        msg_dict['payload'] = payload

        msg_type = self.msg_types[msg_number]

        if DEBUG:
            print(__name__ + ".py")
            print("Peer's message :", msg_number, msg_type)

        self.set_peer_status(msg_dict, msg_type)
        return total_bytes

    def handle_peer_response(self, response):
        data = self.buffer + response
        result = 0

        while data:
            if not self.connection_start:
                result = self.parse_handshake_response(data)
            else:
                result = self.parse_message_response(data)
            if result == 0:
                break
            data = data[result:]
        self.buffer = data

    def set_target_piece_index(self):
        self.target_piece_index = None

    def downloading(self):
        if not self.connection_start:
            self.handshake()
        elif self.peer_choking:
            if DEBUG:
                print(__name__ + ".py")
                print("send interested")
            self.pass_message(msg_type='interested')
        else:
            if not self.torrent.rare_index:
                self.torrent.request_rarest_first()

            piece_index = self.new_piece_index()

            if piece_index is None:
                return

            self.target_piece_index = piece_index

            if DEBUG:
                print(__name__ + ".py")
                print(piece_index)

            self.torrent.piece_request[piece_index].append(self)

            self.request_block(piece_index, None)

    def request_block(self, piece_index, starting_point):
        if starting_point is None:
            starting_point_value = 0
        else:
            starting_point_value = starting_point + CONFIG['block_length']

        last_index = self.pieces - 1

        if piece_index == last_index:
            piece_length = self.torrent.torrent_metadata['info']['piece_length']
            total_length = self.torrent.torrent_metadata['info']['length']
            block_length_value = (total_length - (last_index * piece_length))
            new_block_length = block_length_value - starting_point_value

            if new_block_length < CONFIG['block_length']:
                final_block_length = new_block_length
            else:
                final_block_length = CONFIG['block_length']
        else:
            final_block_length = CONFIG['block_length']

        self.pass_message(msg_type='request', piece_index=piece_index, starting_point=starting_point_value, block_length=final_block_length)

    def find_rarest_index(self):
        min_value = 99999
        rarest_index = 0
        rarest_array_index = None

        for index_entry in (self.torrent.rare_index):
            if index_entry:
                if index_entry[1] < min_value and index_entry[1] != 0:
                    min_value = index_entry[1]
                    rarest_index = index_entry[0]
                    rarest_array_index = index_entry
        return (rarest_index, rarest_array_index)

    def new_piece_index(self):
        for loop_index in range(self.pieces):
            piece_index, rarest_array_tuple = self.find_rarest_index()

            if (self.peer_piece_list[piece_index] and not self.torrent.piece_request[piece_index]):

                if rarest_array_tuple in self.torrent.rare_index or self.torrent.rare_index:
                    self.torrent.set_rarest_index(rarest_array_tuple)

                return piece_index

            elif self.torrent.piece_request[piece_index]:
                self.torrent.set_rarest_index(rarest_array_tuple)
            elif not self.peer_piece_list[piece_index]:
                self.torrent.set_rarest_index(rarest_array_tuple)

        for current_piece_index in range(self.pieces):
            if not self.torrent.current_torrent_download.complete[current_piece_index] and self.peer_piece_list[piece_index]:
                return current_piece_index
        return None

    def set_peer_status(self, msg_dict, msg_type):
        if msg_type == 'choke':
            self.peer_choking = 1
            self.downloading()
        elif msg_type == 'unchoke':
            self.peer_choking = 0
            self.downloading()
        elif msg_type == 'interested':
            self.peer_interested = 1
        elif msg_type == 'not_interested':
            self.peer_interested = 0
        elif msg_type == 'have':
            (piece_index,) = struct.unpack('!L', msg_dict['payload'])
            self.peer_piece_list[piece_index] = 1

        elif msg_type == 'bitfield':
            payload = msg_dict['payload']

            binary_representation = bin(int.from_bytes(payload, byteorder=sys.byteorder))

            if len(binary_representation) < self.pieces:
                for bit_index in range(2, len(binary_representation)):
                    self.peer_piece_list[bit_index - 2] = binary_representation[bit_index]
            else:
                for bit_index in range(2, self.pieces + 2):
                    if bit_index < len(self.peer_piece_list) + 2 and bit_index < len(binary_representation):
                        self.peer_piece_list[bit_index - 2] = int(binary_representation[bit_index])

        elif msg_type == 'piece':
            full_payload = msg_dict['payload']
            (piece_index, block_start) = struct.unpack('!LL', full_payload[:8])
            payload = msg_dict['payload'][8:]

            if DEBUG:
                print(__name__ + ".py")
                print("st_tuple->", piece_index, block_start)

            self.torrent.check_torrent_download_object(self)
            self.torrent.current_torrent_download.check_block(piece_index, block_start, payload)

        elif msg_type == 'cancel':
            print('cancel')
        elif msg_type == 'port':
            print("port")
