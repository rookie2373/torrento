# Driver code for Bittorrent client.

# Import Modules
from connection import con_menu
from torrent import Client_Torrent
from metainfo import getTorrentMetaInfo,getRawFile
from tracker import clientRequest
from datafiles import torrentfiles
import sys

# The Driver Code
if __name__ == '__main__':
    
    # Select filename and extract torrent info
    filename = sys.argv[1]
    contents = getRawFile(filename)
    metainfo = getTorrentMetaInfo(contents)
    torr = Client_Torrent(metainfo,con_menu)
    # print(metainfo)

    # Send request to tracker
    clientRequest(torr,metainfo,metainfo['announce'])
    
    # Connecting to peers using torrent.py
    torr.torrent_conn()
    con_menu.start_loop()
