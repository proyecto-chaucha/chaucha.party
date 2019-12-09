from bitcoin import *
from binascii import hexlify, b2a_hex, a2b_hex
from struct import pack, unpack
from hashlib import new
from chungungo.params import *


def gethexlen(string):
    return '{:02x}'.format(int(len(string)/2))


def getlocktime(script):
    locktime_len = int(script[0:2])
    locktime_packed = script[2: locktime_len*2 + 2]

    if locktime_len < 4:
        locktime_packed += '00'*(4 - locktime_len)

    return unpack('<i', a2b_hex(locktime_packed))[0]


def getScriptAddr(script):
    return scriptaddr(script, 50)


def getfee(array):
    fee = int((base_fee + fee_per_input*len(array))*COIN)
    if fee > max_fee:
        fee = max_fee
    return fee


def getRedeemScript(args):
    if args[0] == 'CLTV':
        type, locktime, privkey = args

        # Create hex-compressed public key
        pubkey = encode_pubkey(privtopub(privkey), 'hex_compressed')

        # little-endian hex packing
        locktime = hexlify(pack('<i', locktime)).decode('utf-8')

        # remove zeros
        locktime = locktime.rstrip('0')
        if len(locktime) % 2 > 0:
            locktime += '0'

        # 33 bytes hex-compressed pubkey
        pubkey = gethexlen(pubkey) + pubkey
        locktime = gethexlen(locktime) + locktime

        # PAY-TO-PUBKEY OP_CHECKLOCKTIMEVERIFY
        script = locktime + OP_CHECKLOCKTIMEVERIFY + OP_DROP + pubkey + OP_CHECKSIG

    elif args[0] == 'HASH256':
        type, solution = args

        # SHA256(SHA256(solution))
        hexsolution = new('sha256', new(
            'sha256', solution.encode()).digest()).hexdigest()

        # OP_HASH256 <hexsolution> OP_EQUAL
        script = OP_HASH256 + gethexlen(hexsolution) + hexsolution + OP_EQUAL

    p2sh_addr = scriptaddr(script, 50)
    return [script, p2sh_addr]


def getPayload(string):
    metadata = bytes(string, 'utf-8')
    metadata_len = len(metadata)

    if metadata_len <= 75:
        payload = bytearray((metadata_len, ))
    elif metadata_len <= 256:
        payload = b"\x4c" + bytearray((metadata_len, ))
    else:
        payload = b"\x4d" + bytearray((metadata_len % 256, ))
        payload += bytearray((int(metadata_len / 256), ))

    return payload + metadata


def maketx(args):
    session, unspent, amount, receptor, op_return = args

    # Parametros de session
    addr = session['address']
    privkey = session['privkey']

    # Transformar valores a Chatoshis
    used_amount = int(amount * COIN)
    used_unspent = int(unspent['used'] * COIN)

    # Input
    inputs = unspent['inputs']

    # Fees
    used_fee = getfee(inputs)

    # Receptor change
    if used_unspent == used_amount:
        tx_value = (used_amount - used_fee)
    else:
        tx_value = used_amount

    # Output
    outputs = []

    # Scripthash vs PubKeyHash
    if receptor[0] == 'M':
        scrpthash = b58check_to_hex(receptor)
        p2sh_script = OP_HASH160 + gethexlen(scrpthash) + scrpthash + OP_EQUAL
        outputs.append({'value': tx_value, 'script': p2sh_script})
    else:
        outputs.append({'address': receptor, 'value': tx_value})

    # Change
    if used_unspent > used_amount + used_fee:
        fee = int(used_unspent - used_amount - used_fee)
        outputs.append({'address': addr, 'value': fee})

    # OP_RETURN
    if len(op_return) > 0 and len(op_return) <= 255:
        payload = getPayload(op_return)
        hex_p = b2a_hex(payload).decode('utf-8', errors='ignore')
        script = '6a' + hex_p
        outputs.append({'value': 0, 'script': script})

    # raw TX
    tx = mktx(inputs, outputs)
    # Signed Raw TX
    for i in range(len(inputs)):
        tx = sign(tx, i, privkey)

    return tx


def P2SHtx(args):
    script, usr, receptor, unspent, balance = args
    addr = getScriptAddr(script)

    # Fee
    ins = unspent['inputs']
    fee = getfee(ins)
    len_inputs = len(ins)

    # Outputs
    out_value = int(balance * COIN) - fee
    outs = [{'address': receptor, 'value': out_value}]

    # Make unsigned transaction
    tx = mktx(ins, outs)

    if 'csrf_token' in usr:
        # Append nLockTime and reset nSequence
        unpacked = deserialize(tx)
        unpacked['locktime'] = getlocktime(script)
        for i in range(len_inputs):
            unpacked['ins'][i]['sequence'] = 0
        tx = serialize(unpacked)

    # sign inputs
    unpacked = deserialize(tx)
    for i in range(len_inputs):
        if 'csrf_token' in usr:
            sig = multisign(tx, i, script, usr['privkey'])
            unpacked['ins'][i]['script'] = gethexlen(sig) + sig
        else:
            hexsolv = b2a_hex(usr.encode()).decode('utf-8')
            unpacked['ins'][i]['script'] = gethexlen(hexsolv) + hexsolv

        # P2SH redeem script
        unpacked['ins'][i]['script'] += gethexlen(script) + script

    return serialize(unpacked)
