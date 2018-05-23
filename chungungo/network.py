from requests import get, post
from bitcoin import *
import binascii
import time

# Network
magic = 88
fee = 0.001
satoshi = 100000000

def gettx(txid):
    url = 'https://explorer.cha.terahash.cl/api/tx/'
    return get(url + txid).json()

def gethistory(addr, page=0):
    url = 'https://explorer.cha.terahash.cl/api/txs/?address='
    history = get(url + addr + '&pageNum=' + str(page)).json()

    txs = []
    for i in history['txs']:
        actual = time.localtime(int(i['time']))
        date = time.strftime('%d.%m.%Y %H:%M:%S', actual)
        msg_str = ''
        for j in i['vout']:
            hex_script = j['scriptPubKey']['hex']
            if hex_script.startswith('6a'):
                if len(hex_script) <= 77*2:
                    sub_script = hex_script[4:]
                else:
                    sub_script = hex_script[6:]

                msg_str = binascii.a2b_hex(sub_script)

        tx = {'confirmations' : i['confirmations'],
              'txid' : i['txid'],
              'time' : date,
              'msg' : msg_str.decode('utf-8', errors='ignore')}

        txs.append(tx)
    pages = history['pagesTotal']
    return [txs, pages]

def getbalance(addr, sendamount=0):
    # Captura de balance por tx sin gastar
    url = 'https://explorer.cha.terahash.cl/api/addr/'
    unspent = get(url + addr + '/utxo').json()

    # Variables auxiliares
    inputs = []
    confirmed = unconfirmed = unspent_balance = 0

    for i in unspent:
        if i['confirmations'] >= 6:
            confirmed += i['amount']

            if sendamount > 0:
                unspent_balance += i['amount']
                inputs_tx = {'output' : i['txid'] + ':' + str(i['vout']),
                             'value' : i['satoshis'],
                             'address' : i['address']}

                inputs.append(inputs_tx)

                if unspent_balance > int(sendamount):
                    break
        else:
            unconfirmed += i['amount']

    if sendamount > 0:
        unspent = {'used' : round(unspent_balance, 8), 'inputs' : inputs}
        return unspent
    else:
        return [confirmed, unconfirmed]


def broadcast(session, unspent, amount, receptor, op_return):
    # Parametros de session
    addr = session['address']
    privkey = session['privkey']

    # Transformar valores a Chatoshis
    used_amount = int(amount*satoshi)
    used_unspent = int(unspent['used']*satoshi)

    # Input
    inputs = unspent['inputs']

    # Calculo de fee
    used_fee = int(fee*satoshi*(len(inputs)/5 + 1))

    # Output
    outputs = []

    # Receptor
    if used_unspent == used_amount:
        tx_value = (used_amount - used_fee)
    else:
        tx_value = used_amount

    outputs.append({'address' : receptor, 'value' : tx_value})

    # Change
    if used_unspent > used_amount + used_fee:
        fee = int(used_unspent - used_amount - used_fee)
        outputs.append({'address' : addr, 'value' : fee})

    # OP_RETURN
    if len(op_return) > 0 and len(op_return) <= 255:
        payload = OP_RETURN_payload(op_return)
        hex_p = binascii.b2a_hex(payload).decode('utf-8', errors='ignore')
        script = '6a' + hex_p

        outputs.append({'value' : 0, 'script' : script})

    # creación de transacción
    tx = mktx(inputs, outputs)

    # Firma de cada output
    for i in range(len(inputs)):
        tx = sign(tx, i, privkey)

    url = 'https://explorer.cha.terahash.cl/api/tx/send'
    broadcasting = post(url, data={'rawtx' : tx})

    return broadcasting

def OP_RETURN_payload(string):
    metadata = bytes(string, 'utf-8')
    metadata_len = len(metadata)

    if metadata_len<=75:
        payload = bytearray((metadata_len,))
    elif metadata_len<=256:
        payload = b"\x4c" + bytearray((metadata_len,))
    else:
        payload = b"\x4d" + bytearray((metadata_len%256,))
        payload += bytearray((int(metadata_len/256),))

    return payload + metadata
