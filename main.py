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