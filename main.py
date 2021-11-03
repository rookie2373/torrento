# Driver code for Bittorrent client.

# Import Modules
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
    print(metainfo['info']['name'])

    # Send request to tracker
    clientRequest(metainfo)

#from metainfo import getTorrentMetaInfo,getRawFile
# from tracker import client_request
# from connection import con_menu
# from torrent import Client_Torrent



# if __name__ == '__main__':
#     filename = torrentfiles[9]
#     contents = getRawFile(filename)
#     metainfo = getTorrentMetaInfo(contents)
#     torr = Client_Torrent(metainfo,con_menu)
#     client_request(torr,metainfo,metainfo['announce'])
#     con_menu.start_loop()
