# Driver code for Bittorrent client.

# Import Modules
from metainfo import getTorrentMetaInfo,getRawFile
from tracker import clientRequest
from torrents import torrentfiles
import sys

# The Driver Code
if __name__ == '__main__':
    # Select filename and extract torrent info
    filename = torrentfiles[5]
    contents = getRawFile(filename)
    metainfo = getTorrentMetaInfo(contents)
    print(metainfo['info']['name'])

    # Send request to tracker
    clientRequest(metainfo)

# from torrent_metainfo import TorrentMetainfo
# from tracker import client_request
# from connection import con_menu
# from torrent import Client_Torrent

# def get_metaifo(filename):
#     print(filename)
#     with open(filename,'rb') as file:
#         contents = file.read()
#         return contents


# if __name__ == '__main__':
#     filename = r"C:\CN\Bittorrent_project\share\flagfromserver.torrent"
#     contents = get_metainfo(filename)
#     metainfo = TorrentMetainfo(contents)
#     torr = Client_Torrent(metainfo,con_menu)
#     client_request(torr,metainfo,metainfo['announce'])