
import hashlib
import logging
from config import DEBUG
from writedata import WriteData

logger = logging.getLogger(__name__)


class TorrentDownload():
    def __init__(self, peer, torrent):
        logger.debug(f"TorrentDownload initialized for peer {peer.ip}:{peer.port}")
        self.peer = peer
        self.torrent = torrent

        self.complete = self.torrent.completed_pieces
        self.chunks = self.torrent.chunks

    def check_block(self, piece_index, chunk_start, payload):
        if self.complete[piece_index]:
            logger.debug(f"Piece {piece_index} already completed")
            print("this chunks is finished")
            return

        for chunk_entry in self.chunks[piece_index]:
            if chunk_entry[0] == chunk_start:
                print("Already present")
                self.peer.request_block(piece_index, chunk_start)
                return

        self.chunks[piece_index].append(
            (chunk_start, payload))
        last_index = self.peer.pieces - 1

        if piece_index == last_index:
            piece_length = self.torrent.torrent_metadata['info']['piece_length']
            total_length = self.torrent.torrent_metadata['info']['length']
            block_length = (total_length - (last_index * piece_length))
            required_len = block_length
        else:
            required_len = self.torrent.torrent_metadata['info']['piece_length']

        current_length = self.sum_piece_length(piece_index)
        logger.debug(f"Piece {piece_index}: {current_length}/{required_len} bytes")

        if current_length == required_len:
            self.verify_hash(piece_index)
        else:
            self.peer.request_block(piece_index, chunk_start)

    def sum_piece_length(self, current_piece_index):
        total_sum = 0
        for chunk_entry in self.chunks[current_piece_index]:
            total_sum += len(chunk_entry[1])
        return total_sum

    def verify_hash(self, piece_index):
        logger.debug(f"Verifying hash for piece {piece_index}")
        self.chunks[piece_index].sort(key=lambda x: x[0])
        blocks = []

        for chunk_entry in self.chunks[piece_index]:
            blocks.append(chunk_entry[1])

        current_piece = bytes(byte for block in blocks for byte in block)

        current_piece_sha = hashlib.sha1(current_piece).digest()

        file_shas = self.torrent.torrent_metadata['info']['pieces']
        file_index_sha = file_shas[piece_index]

        if file_index_sha != current_piece_sha:
            logger.error(f"Hash mismatch for piece {piece_index}")
            print("SHA hash doesn't match")
            return
        else:
            self.mark_piece_complete(piece_index, current_piece)

    def mark_piece_complete(self, piece_index, current_piece):
        logger.info(f"Marking piece {piece_index} as complete")
        self.torrent.store_piece(piece_index, current_piece)

        for peer in self.torrent.piece_request[piece_index]:
            if peer.target_piece_index == piece_index:
                peer.set_target_piece_index()

        self.torrent.piece_request[piece_index] = 1
        self.display_download()
        self.peer.downloading()

        if self.check_download_complete():
            self.torrent.connection_manager.end_loop()
            self.write_data()
        else:
            return

    def display_download(self):
        pieces_sum = 0
        for piece in self.complete:
            if piece:
                pieces_sum += 1
        pieces_length = len(self.complete)
        up_to_complete = 100.0 * pieces_sum / pieces_length
        
        # Create progress bar
        bar_length = 40
        completed_bars = int((up_to_complete / 100) * bar_length)
        remaining_bars = bar_length - completed_bars
        progress_bar = '█' * completed_bars + '░' * remaining_bars
        
        # Display with nice formatting
        print(f'\r[{progress_bar}] {up_to_complete:6.1f}% ({pieces_sum}/{pieces_length} pieces)', end='', flush=True)

    def check_download_complete(self):
        for piece in self.complete:
            if piece:
                continue
            else:
                return 0
        return 1

    def write_data(self):
        self.torrent.complete = 1
        self.close_peer_connections()

        write_data_obj = WriteData(self.torrent, self.complete)

        if self.torrent.torrent_metadata['info']['format'] == 'single file':
            write_data_obj.for_single_file()
        else:
            write_data_obj.for_multiple_file()

    def close_peer_connections(self):
        for peer in self.torrent.peer_list:
            if peer.connection:
                peer.connection.close_connection()
        return