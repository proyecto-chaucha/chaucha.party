from chungungo.functions import *
from requests import get, post
from binascii import a2b_hex
from time import localtime, strftime
from chungungo import app

def broadcast(tx):
    url = app.config['API_URL'] + '/api/tx/send'
    broadcasting = post(url, data={'rawtx' : tx})

    return broadcasting


def checklocktime(script):
    url = app.config['API_URL'] + '/api/status?getInfo'
    last_block = get(url).json()['info']['blocks']
    locktime = getlocktime(script)

    return int(last_block) >= int(locktime)


def gethistory(addr, page=0):
    url = app.config['API_URL'] + '/api/txs/?address='
    history = get(url + addr + '&pageNum=' + str(page)).json()

    txs = []
    for i in history['txs']:
        actual = localtime(int(i['time']))
        date = strftime('%d.%m.%Y %H:%M:%S', actual)
        msg = ''
        for j in i['vout']:
            hex_script = j['scriptPubKey']['hex']
            if hex_script.startswith('6a'):
                if len(hex_script) <= 77*2:
                    sub_script = hex_script[4:]
                else:
                    sub_script = hex_script[6:]

                msg = a2b_hex(sub_script).decode('utf-8', errors='ignore')

        tx = {'confirmations' : i['confirmations'],
              'txid' : i['txid'],
              'time' : date,
              'msg' : msg}

        txs.append(tx)
    return [txs, history['pagesTotal']]


def getbalance(addr):
    url = app.config['API_URL'] + '/api/addr/'
    balance = get(url + addr).json()
    return round(float(balance['balance']), 8)


def getunspent(addr, sendamount=0):
    # Captura de balance por tx sin gastar
    url = app.config['API_URL'] + '/api/addr/'
    try:
        unspent = get(url + addr + '/utxo').json()
    except:
        return False

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
                if unspent_balance >= int(sendamount):
                    break
        else:
            unconfirmed += i['amount']
    if sendamount > 0:
        return {'used' : round(unspent_balance, 8), 'inputs' : inputs}
    else:
        return [confirmed, unconfirmed]
