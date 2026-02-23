import sys
from config import DEBUG
from metainfo import get_torrent_meta_info, get_raw_file
from tracker import client_request
from connection import connection_manager
from torrent import ClientTorrent

if __name__ == '__main__':
    if DEBUG:
        print("[main.py] Starting torrent client")
    filename = sys.argv[1]
    if DEBUG:
        print(f"[main.py] Loading torrent file: {filename}")
    contents = get_raw_file(filename)
    if DEBUG:
        print(f"[main.py] Torrent file loaded, size: {len(contents)} bytes")
    meta_info = get_torrent_meta_info(contents)
    if DEBUG:
        print(f"[main.py] Metadata extracted: {meta_info['info']['name']}")

    torrent = ClientTorrent(meta_info, connection_manager)
    if DEBUG:
        print("[main.py] ClientTorrent initialized")

    client_request(torrent, meta_info, meta_info['announce'])
    if DEBUG:
        print(f"[main.py] Tracker request completed, {len(torrent.peer_list)} peers found")

    torrent.connect_to_peers()
    if DEBUG:
        print(f"[main.py] Connecting to {len(torrent.peer_list)} peers")
    connection_manager.start_loop()