import os
import logging
from config import DEBUG

logger = logging.getLogger(__name__)

class WriteData():
    def __init__(self, torrent, piece_list):
        logger.debug("WriteData initialized for torrent")
        self.torrent = torrent
        self.piece_list = piece_list
        self.data = []
        self.piece_list_to_data()
        self.data = bytes(self.data)

    def piece_list_to_data(self):
        for piece_entry in self.piece_list:
            for byte_value in piece_entry:
                self.data.append(byte_value)

    def for_single_file(self):
        logger.info("Writing single file")
        head, tail = os.path.split(self.torrent.torrent_metadata['info']['name'])
        filename = tail
        current_dir = os.getcwd()
        file_path = os.path.join(current_dir, filename)
        with open(file_path, 'wb') as file_handle:
            file_handle.write(self.data)
        print(f"File downloaded at location {file_path}")

    def for_multiple_file(self):
        logger.info("Writing multiple files")
        current_dir = os.getcwd()
        head, tail = os.path.split(self.torrent.torrent_metadata['info']['name'])
        filename = tail
        start_position = 0
        for file_data in self.torrent.torrent_metadata['info']['files']:
            file_path = os.path.join(current_dir, file_data['path'])
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            data = self.data[start_position:start_position + file_data['length']]
            file_handle = open(file_path, 'wb')
            file_handle.write(data)
            start_position += file_data['length']
            logger.debug(f"Wrote {file_path}")

        print("Files saved")



