from metainfo import getTorrentMetaInfo,getRawFile
from tracker import client_request
from torrents import torrentfiles

if __name__ == '__main__':
    filename = torrentfiles[9]
    contents = getRawFile(filename)
    metainfo = getTorrentMetaInfo(contents)

    client_request(metainfo,metainfo['announce'])