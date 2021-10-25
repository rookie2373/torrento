from torrent_metainfo import TorrentMetainfo
from tracker import client_request
from connection import con_menu
from torrent import Client_Torrent

def get_metaifo(filename):
    print(filename)
    with open(filename,'rb') as file:
        contents = file.read()
        return contents


if __name__ == '__main__':
    filename = r"C:\CN\Bittorrent_project\share\flagfromserver.torrent"
    contents = get_metainfo(filename)
    metainfo = TorrentMetainfo(contents)
    torr = Client_Torrent(metainfo,con_menu)
    client_request(torr,metainfo,metainfo['announce'])
