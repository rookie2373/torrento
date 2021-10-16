import os
import copy
import hashlib
from pprint import pformat
import bencodepy
import voluptuous as vol

meta_struct = {}

def TorrentMetainfo(bencoded_data):
    # check file is empty or not
    if not bencoded_data:
        print("Error :file is empty")
    else:

        # deconding the bendcoded data into string
        meta_data = bencodepy.decode(bencoded_data)

        # endcoding field has the string encoding format which is used to generate pieces part of info dictionary
        encode = meta_data.get(b'encoding')
        meta_struct['encoding'] = encode

        # meta_data contain accounce varible of dictionary which assigned the url of trackers
        announce = meta_data.get(b'announce')
        meta_struct['announce'] = announce

        # meta_data also contain field creation date , comment , created by and announced_list
        # but we are ignoring this field because these are optionals

        info = meta_data.get(b'info')  # info here is dictoctionaru

        # crypting the info using secure hash algorithm  and were digest return encoded data in bytes
        info_hash = hashlib.sha1(bencodepy.encode(info)).digest()

        info_data = decode_info(info)
        meta_struct['info'] = info_data
        meta_struct['info_hash'] = info_hash

        return repr_in_meta_struct()


def decode_info(info):
    info_dict = {}
    # piece length is number of byte in each piece
    info_dict['piece_length'] = info[b'piece length']

    Sha1_len = 20
    # pieces consisisting of the concatenation of all 20-byte sha1 hash value
    pieces = info[b'pieces']
    pieces_list = []
    for k in range(0, len(pieces), Sha1_len):
        pieces_list.append(pieces[k:k + Sha1_len])  # making the each piece of 20 byte

    info_dict['pieces'] = pieces_list

    name = info[b'name'].decode('utf-8')

    info_dict['name'] = name

    files_dict = info.get(b'files')  # files is field which contains the key .i.e length , md5sum, path

    # checking single or multiple file
    if not files_dict:
        info_dict['format'] = 'single file'
        info_dict['files'] = None  # in single file mode there no dictionary for files
        info_dict['length'] = info[b'length']
    else:
        info_dict['format'] = 'multiple file'
        info_dict['file'] = []
        
        for j in files_dict[b'files']:
            Path = []
            # path field conataining one or more string which presents path and filename which in bencoded
            for k in j[b'path']:
                Path.append(k.decode('utf-8'))
            info_dict['files'].append(
                {
                    'length': j[b'length'],
                    'path': os.path.join(*Path)
                }
            )
        info_dict['length'] = sum(f['length'] for f in info_dict['files'])

    return info_dict


# it will represent the meta dict in structured format
def repr_in_meta_struct():
    # coping the orignal info_dict
    temp_dict = copy.deepcopy(meta_struct)
    if len(temp_dict['info']['pieces']) > 3:
        temp_dict['info']['pieces'] = temp_dict['info']['pieces'][:3] + ['...']
    if temp_dict['info']['files'] and len(temp_dict['info']['files']) > 3:
        temp_dict['info']['files'] = temp_dict['info']['files'][:3] + ['...']
    return temp_dict


def get_piece_lenght(index, ):
    pass
