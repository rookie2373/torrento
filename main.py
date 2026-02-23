import sys
import logging
from config import DEBUG
from metainfo import get_torrent_meta_info, get_raw_file
from tracker import client_request
from connection import connection_manager
from torrent import ClientTorrent

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Starting torrent client")
    filename = sys.argv[1]
    logger.debug(f"Loading torrent file: {filename}")
    contents = get_raw_file(filename)
    logger.debug(f"Torrent file loaded, size: {len(contents)} bytes")
    meta_info = get_torrent_meta_info(contents)
    logger.info(f"Metadata extracted: {meta_info['info']['name']}")

    torrent = ClientTorrent(meta_info, connection_manager)
    logger.debug("ClientTorrent initialized")

    client_request(torrent, meta_info, meta_info['announce'])
    logger.info(f"Tracker request completed, {len(torrent.peer_list)} peers found")

    torrent.connect_to_peers()
    logger.info(f"Connecting to {len(torrent.peer_list)} peers")
    connection_manager.start_loop()