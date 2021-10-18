from metainfo import TorrentMetainfo
from tracker import client_request

def get_metaifo(filename):
    print(filename)
    with open(filename,'rb') as file:
        contents = file.read()
        return contents


if __name__ == '__main__':
    filename = "./Torrentfiles/flagfromserver.torrent"
    contents = get_metaifo(filename)
    metainfo = TorrentMetainfo(contents)

    client_request(metainfo,metainfo['announce'])