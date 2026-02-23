import os
import copy
import hashlib
import bencodepy
import random
import logging
from config import DEBUG, MB_FACTOR

logger = logging.getLogger(__name__)

META_INFO = {}

def get_raw_file(filename):
    logger.debug(f"Loading file: {filename}")
    try:
        with open(filename, 'rb') as f:
            contents = f.read()
            logger.debug(f"File loaded successfully, size: {len(contents)} bytes")
            return contents
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        raise

def get_torrent_meta_info(bencode_data):
    if not bencode_data:
        logger.error("File is empty")
        return None
    logger.debug("Decoding bencode data")
    try:
        meta_data = bencodepy.decode(bencode_data)
        logger.debug(f"Bencode decoded, type: {type(meta_data)}")

        encoding = meta_data.get(b'encoding')
        META_INFO['encoding'] = encoding
        logger.debug(f"Encoding: {encoding}")

        announce = meta_data.get(b'announce')
        META_INFO['announce'] = announce

        if not announce:
            logger.debug("Using announce-list")
            announce_list = meta_data.get(b'announce-list')
            META_INFO['announce_list'] = announce_list
            META_INFO['announce'] = announce_list[3]

        logger.debug(f"Announce: {META_INFO['announce']}")

        info = meta_data.get(b'info')

        logger.debug("Processing info dict")

        info_hash = hashlib.sha1(bencodepy.encode(info)).digest()
        logger.debug(f"Info hash: {info_hash.hex()[:16]}...")

        info_data = process_file_info(info)

        META_INFO['info'] = info_data
        META_INFO['info_hash'] = info_hash
        logger.debug("Metadata extraction complete")

        return META_INFO
    except Exception as e:
        logger.error(f"Error decoding metadata: {str(e)}")
        raise

def process_file_info(file_info):
    logger.debug("Processing file info")
    info_dict = {}

    info_dict['piece_length'] = file_info[b'piece length']

    logger.debug(f"Piece length: {info_dict['piece_length'] / MB_FACTOR:.2f} MB")

    SHA1_LENGTH = 20
    pieces = file_info[b'pieces']

    if DEBUG:
        print(type(pieces))

    piece_list = []
    for offset in range(0, len(pieces), SHA1_LENGTH):
        piece_list.append(pieces[offset:offset + SHA1_LENGTH])

    info_dict['pieces'] = piece_list

    logger.debug(f"Total pieces: {len(piece_list)}")

    name = file_info[b'name'].decode('utf-8')
    info_dict['name'] = name

    logger.debug(f"Torrent name: {name}")

    files_dict = file_info.get(b'files')

    logger.debug(f"Files dictionary present: {files_dict is not None}")

    if not files_dict:
        info_dict['format'] = 'single file'
        info_dict['files'] = None
        info_dict['length'] = file_info[b'length']

        logger.debug(f"Single file torrent, size: {info_dict['length'] / MB_FACTOR:.2f} MB")

    else:
        info_dict['format'] = 'multiple file'
        info_dict['files'] = []

        for file_data in files_dict:
            path = []

            logger.debug(f"Processing file with path components: {file_data.get(b'path', [])}")

            for location in file_data[b'path']:
                path.append(location.decode('utf-8'))

            info_dict['files'].append(
                {
                    'length': file_data[b'length'],
                    'path': os.path.join(*path)
                }
            )

        logger.debug(f"Multiple file torrent, total files: {len(info_dict['files'])}")

        length = sum(file_data["length"] for file_data in info_dict['files'])
        info_dict['length'] = length

        logger.debug(f"Total size: {info_dict['length'] / MB_FACTOR:.2f} MB")

    return info_dict
