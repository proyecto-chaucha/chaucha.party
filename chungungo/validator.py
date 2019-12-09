# http://rosettacode.org/wiki/Bitcoin/address_validation#Python
from hashlib import sha256

digits58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def decode_base58(bc, length):
    n = 0
    for char in bc:
        n = n * 58 + digits58.index(char)
    return n.to_bytes(length, 'big')


def check_bc(bc):
    try:
        bcb = decode_base58(bc, 25)
        return bcb[-4:] == sha256(sha256(bcb[:-4]).digest()).digest()[:4]
    except Exception:
        return False
