import hashlib
from Write_data import Write_data


class torr_Download():
    def __init__(self, peer, torr):
        self.peer = peer
        self.torr = torr
        self.complete = self.torr.Completed_pieces  # for collecting the all downlaoded piece
        self.chunks = self.torr.chunks


    def check_block(self, piece_inx, chunk_start, payload):
        # checking if recv block is already present or not

        if self.complete[piece_inx]:
            print("this chunks is finished")
            return
        for i in self.chunks[piece_inx]:
            if i[0] == chunk_start:  # if starting point of recv block is already present then we request next block
                print("Already present")
                self.peer.request_Block(piece_inx, chunk_start)
                return

        self.chunks[piece_inx].append(
            (chunk_start, payload))  # storing the tuple of starting point pf paylosd with payload at that indx
        last_inx = self.peer.pieces_length - 1

        if piece_inx == last_inx:
            # piece index is last then we need to update the required length
            len_piece = self.torr.meta_struct['info']['piece_length']
            total_length = self.torr.meta_struct['info']['length']
            len_block = (total_length - (last_inx * len_piece))
            required_len = len_block
        else:
            required_len = self.torr.meta_struct['info']['piece_length']
        curre_len = self.sum_piecelen(piece_inx)
        print(required_len, curre_len)
        # checking the piece length of .torrent file is same as total received block length
        if curre_len == required_len:
            self.check_hashvalue(piece_inx)
        else:
            # here we change starting point of block
            self.peer.request_Block(piece_inx,
                                    chunk_start)  # requesting the next block as we requesting the pieces in blocks
            pass

    # adding the each blocks length
    def sum_piecelen(self, curr_piece_inx):
        sum = 0
        for x in self.chunks[curr_piece_inx]:
            sum += len(x[1])
        return sum

    def check_hashvalue(self, piece_inx):
        # sorting the collected piece so that it is in ordered
        self.chunks[piece_inx].sort(key=lambda x: x[0])
        blocks = []
        for k in self.chunks[piece_inx]:
            blocks.append(k[1])
        current_piece = bytes(y for x in blocks for y in x)
        curr_piece_sha = hashlib.sha1(current_piece).digest()

        file_shas = self.torr.meta_struct['info']['pieces']
        file_inx_sha = file_shas[piece_inx]

        if file_inx_sha != curr_piece_sha:
            print("Sha doesn't  match")
            return
        else:
            self.curr_piece_Complete(piece_inx, current_piece)

    def curr_piece_Complete(self, piece_inx, current_piece):

        # assigning zero to the index whose piece we received succesfully and storing the current piece
        self.torr.store_piece(piece_inx,current_piece)

        for peer in self.torr.piece_request[piece_inx]:
            if peer.target_piece_inx == piece_inx:
                peer.set_taget_piece_inx()

        self.torr.piece_request[piece_inx] = 1  # we done with this piece
        self.display_download()
        self.peer.downloading()
        if self.check_download_complete():
            self.torr.con_menu.end_loop()  # end the loop which is running for checking data
            self.write_data()
        else:
            return

    def display_download(self):
        pieces_sum = 0
        print("downloaded",len(self.complete))
        for piece in self.complete:
            if piece:
                pieces_sum += 1
        pieces_len = len(self.complete)
        upto_complete = 100.0 * pieces_sum / pieces_len
        print('%02.1f%% complete' % upto_complete)

    def check_download_complete(self):
        for piece in self.complete:
            if piece:
                continue
            else:
                return 0
        return 1

    def write_data(self):
        self.torr.complete = 1
        # now closing all peer connection
        self.close_peer_conn()
        WD = Write_data(self.torr, self.complete)
        if self.torr.meta_struct['info']['format'] == 'single file':
            WD.for_single_file()
        else:
            WD.for_multiple_file()

    def close_peer_conn(self):
        for peer in self.torr.peer_list:
            if peer.con:
                peer.con.Close_connection()
        return
