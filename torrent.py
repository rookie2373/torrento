
from peers import Peers
from download import TorrentDownload
from config import CONFIG, DEBUG
import time
import logging

logger = logging.getLogger(__name__)

class ClientTorrent():
    def __init__(self, torrent_metadata, connection_manager):
        logger.info(f"ClientTorrent initialized for: {torrent_metadata['info']['name']}")
        self.torrent_metadata = torrent_metadata
        self.connection_manager = connection_manager
        self.present_peers = []
        self.peer_list = []

        self.complete = False

        self.piece_request = [[] for piece in
                              self.torrent_metadata['info']['pieces']]

        self.torrent_download_list = []
        self.current_torrent_download = None

        self.connection_failed_history = []
        self.completed_pieces = [0 for piece in torrent_metadata['info']['pieces']]

        self.chunks = [[] for piece in self.torrent_metadata['info']['pieces']]
        self.rare_index = []

    def connect_to_peers(self):
        logger.info(f"Connecting to peers, max_peers: {CONFIG['max_peers']}, available: {len(self.peer_list)}")
        peer_list_length = len(self.peer_list)
        peer_count = 0

        while (peer_count < CONFIG['max_peers'] and peer_count < len(self.peer_list)):
            logger.debug(f"Connecting to peer {peer_count+1}/{min(CONFIG['max_peers'], len(self.peer_list))}")
            self.peer_list[peer_count].make_connection()
            self.current_torrent_download = self.torrent_download_list[peer_count]
            peer_count += 1

    def make_peer_list(self, peer_dict):
        each_peer = self.check_peer(**peer_dict)

        if each_peer:
            logger.debug(f"Peer {peer_dict['ip']}:{peer_dict['port']} already in list")
            return each_peer

        logger.debug(f"Adding new peer: {peer_dict['ip']}:{peer_dict['port']}")
        peer = Peers(self, **peer_dict)
        torrent_obj = TorrentDownload(peer, self)

        self.torrent_download_list.append(torrent_obj)
        self.peer_list.append(peer)

        return peer

    def check_peer(self, ip, port, peer_id=None):
        for peer_collection in (self.present_peers, self.peer_list):
            for peer in peer_collection:
                if peer.ip == ip and peer.port == port:
                    return peer
        return False

    def check_torrent_download_object(self, peer):
        for peer_index in range(len(self.peer_list)):
            if self.peer_list[peer_index] == peer:
                self.current_torrent_download = self.torrent_download_list[peer_index]

    def peer_stopped_recovery(self):
        logger.debug("Peer recovery initiated")
        if self.complete:
            return

        for peer in self.peer_list:
            if not peer.connection_failed:
                continue

            if peer in self.connection_failed_history:
                continue
            self.connection_failed_history.append(peer)

            while not peer.connection:
                try:
                    peer.make_connection()
                    peer.connection = 1
                    logger.info(f"Starting new peer connection: {peer.ip}:{peer.port}")
                except Exception as e:
                    logger.error(f"Failed to connect to peer {peer.ip}:{peer.port}: {str(e)}")
                    time.sleep(2)

            if peer.connection:
                break
        return

    def store_piece(self, piece_index, data):
        logger.debug(f"Storing piece {piece_index}, {len(data)} bytes")
        self.completed_pieces[piece_index] = data
        self.chunks[piece_index] = 0

    def get_connection_count(self):
        count = 0
        for peer in self.peer_list:
            if peer.connection:
                count += 1
        return count

    def request_rarest_first(self):
        total_pieces = len(self.torrent_metadata['info']['pieces'])

        for piece_index in range(total_pieces):
            connection_count = self.get_connection_count()
            peer_index = 0
            peer_count = 0

            while (peer_index < connection_count):
                if self.peer_list[peer_index].peer_piece_list[piece_index]:
                    peer_count += 1
                peer_index += 1
            self.rare_index.append((piece_index, peer_count))

    def set_rarest_index(self, index_tuple):
        if self.rare_index and index_tuple in self.rare_index:
            self.rare_index.remove(index_tuple)