from  config import  CONFIG

class torr_Download():
    def __init__(self,peer,torr):
        self.peer = peer
        self.torr = torr
        self.complete = []

        self.set_zero()
        self.chunks = [[] for i in range(self.peer.pieces_length)]


    def set_zero(self):
        for i in range(self.peer.pieces_length):
            self.complete.append(0)


    def check_block(self,piece_inx,chunk_start,payload):
        # checking if recv block is already present or not

        for i in self.chunks[piece_inx]:
            if i[0] == chunk_start: # if starting point of recv block is already present then we request next block
                self.peer.request_Block(piece_inx)
                return

        self.chunks[piece_inx].append((chunk_start,payload)) # storing the tuple of starting point pf paylosd with payload
        required_len =self.torr.meta_struct['info']['piece_length']
        curre_len = self.sum_piecelen(piece_inx)

       # checking the piece length of .torrent file is same as total received block length
        if curre_len == required_len :
            self.check_hashvalue(piece_inx)
        else:
            # here we change starting point of block
            self.peer.request_Block(piece_inx) # requesting the next block as we requesting the pieces in blocks
            pass

    #adding the each blocks length
    def sum_piecelen(self,curr_piece_inx):
        sum = 0
        for x in self.chunks[curr_piece_inx]:
            sum += len(x[1])
        return sum

    def check_hashvalue(self,piece_inx):
        self.chunks[piece_inx].sort(key=lambda x:x[0]) # sorting according to the piece length
        blocks = []
        for k in self.chunks[piece_inx]:
            blocks.append(k[1])

        current_piece = bytes(y for x in blocks for y in x)
        for u in self.chunks[piece_inx]:
            print(u[0])
        piece_sha =  hashlib.sha1(current_piece).digest()

        file_shas = self.torr.meta_struct['info']['pieces']
        curr_inx_sha = file_shas[piece_inx]

        if piece_sha != curr_inx_sha :
            print("Sha doesn't  match")
            return
        else:
            print("match")







