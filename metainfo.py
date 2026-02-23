import os
import copy
import hashlib
import bencodepy
import random
from config import DEBUG, MB_FACTOR

META_INFO = {}

def get_raw_file(filename):
    if DEBUG:
        print(f"[metainfo.py] Loading file: {filename}")
    try:
        with open(filename, 'rb') as f:
            contents = f.read()
            if DEBUG:
                print(f"[metainfo.py] File loaded successfully, size: {len(contents)} bytes")
            return contents
    except FileNotFoundError:
        if DEBUG:
            print(f"[metainfo.py] ERROR: File not found: {filename}")
        raise

def get_torrent_meta_info(bencode_data):
    if not bencode_data:
        print("[metainfo.py] ERROR: File is empty")
        return None
    if DEBUG:
        print("[metainfo.py] Decoding bencode data")
    try:
        meta_data = bencodepy.decode(bencode_data)
        if DEBUG:
            print(f"[metainfo.py] Bencode decoded, type: {type(meta_data)}")

        encoding = meta_data.get(b'encoding')
        META_INFO['encoding'] = encoding
        if DEBUG:
            print(f"[metainfo.py] Encoding: {encoding}")

        announce = meta_data.get(b'announce')
        META_INFO['announce'] = announce

        if not announce:
            if DEBUG:
                print("[metainfo.py] Using announce-list")
            announce_list = meta_data.get(b'announce-list')
            META_INFO['announce_list'] = announce_list
            META_INFO['announce'] = announce_list[3]

        if DEBUG:
            print(f"[metainfo.py] Announce: {META_INFO['announce']}")

        info = meta_data.get(b'info')

        if DEBUG:
            print("[metainfo.py] Processing info dict")

        info_hash = hashlib.sha1(bencodepy.encode(info)).digest()
        if DEBUG:
            print(f"[metainfo.py] Info hash: {info_hash.hex()[:16]}...")

        info_data = process_file_info(info)

        META_INFO['info'] = info_data
        META_INFO['info_hash'] = info_hash
        if DEBUG:
            print(f"[metainfo.py] Metadata extraction complete")

        return META_INFO
    except Exception as e:
        if DEBUG:
            print(f"[metainfo.py] ERROR decoding metadata: {str(e)}")
        raise

def process_file_info(file_info):
    if DEBUG:
        print("[metainfo.py] Processing file info")
    info_dict = {}

    info_dict['piece_length'] = file_info[b'piece length']

    if DEBUG:
        print(f"[metainfo.py] Piece length: {info_dict['piece_length'] / MB_FACTOR:.2f} MB")

    SHA1_LENGTH = 20
    pieces = file_info[b'pieces']

    if DEBUG:
        print(type(pieces))

    piece_list = []
    for offset in range(0, len(pieces), SHA1_LENGTH):
        piece_list.append(pieces[offset:offset + SHA1_LENGTH])

    info_dict['pieces'] = piece_list

    if DEBUG:
        print(info_dict['pieces'])

    name = file_info[b'name'].decode('utf-8')
    info_dict['name'] = name

    if DEBUG:
        print(info_dict['name'])

    files_dict = file_info.get(b'files')

    if DEBUG:
        print(files_dict)

    if not files_dict:
        info_dict['format'] = 'single file'
        info_dict['files'] = None
        info_dict['length'] = file_info[b'length']

        if DEBUG:
            print(str(info_dict['length'] / MB_FACTOR) + " MB")

    else:
        info_dict['format'] = 'multiple file'
        info_dict['files'] = []

        for file_data in files_dict:
            path = []

            if DEBUG:
                print(file_data)
                print()
                print()
                print()

            for location in file_data[b'path']:
                path.append(location.decode('utf-8'))

                if DEBUG:
                    print(location)

            info_dict['files'].append(
                {
                    'length': file_data[b'length'],
                    'path': os.path.join(*path)
                }
            )

        if DEBUG:
            print(info_dict["files"])

        length = sum(file_data["length"] for file_data in info_dict['files'])
        info_dict['length'] = length

        if DEBUG:
            print(str(info_dict['length'] / MB_FACTOR) + " MB")

    return info_dict
