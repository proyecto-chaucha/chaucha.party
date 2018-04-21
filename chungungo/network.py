from requests import get, post
from bitcoin import *
import binascii
import time

# Network
magic = 88
fee = 0.001
satoshi = 100000000

def gethistory(addr):
	history = get('https://explorer.cha.terahash.cl/api/txs/?address=' + addr).json()
	txs = []
	for i in history['txs']:
		date = time.strftime('%d.%m.%Y %H:%M:%S', time.localtime(int(i['time'])))
		tx = {'confirmations' : i['confirmations'], 'txid' : i['txid'], 'time' : date}
		txs.append(tx)
	return txs

def getbalance(addr):
	# Captura de balance por tx sin gastar
	unspent = get('https://explorer.cha.terahash.cl/api/addr/' + addr + '/utxo').json()
		
	confirmed = unconfirmed = 0

	for i in unspent:
		if i['confirmations'] >= 6:
			confirmed += i['amount']
		else:
			unconfirmed += i['amount']

	return [confirmed, unconfirmed]


def getunspent(addr, sendamount):
	# Captura de balance por tx sin gastar
	unspent = get('https://explorer.cha.terahash.cl/api/addr/' + addr + '/utxo').json()

	inputs = []
	unspent_balance = 0

	for i in unspent:
		if i['confirmations'] >= 6:
			unspent_balance += i['amount']
			inputs_tx = {'output' : i['txid'] + ':' + str(i['vout']), 'value' : i['satoshis'], 'address' : i['address']}
			inputs.append(inputs_tx)
			if unspent_balance > int(sendamount):
				break

	unspent = {'used' : round(unspent_balance, 8), 'inputs' : inputs}
	return unspent

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
	used_fee = int(fee*satoshi*(len(inputs)/4 + 1))
	
	# Output
	outputs = []

	# Receptor
	if used_unspent == used_amount:
		outputs.append({'address' : receptor, 'value' : (used_amount - used_fee)})
	else:
		outputs.append({'address' : receptor, 'value' : used_amount})
		
	# Change
	if used_unspent > used_amount + used_fee:
		outputs.append({'address' : addr, 'value' : int(used_unspent - used_amount - used_fee)})

	# OP_RETURN
	if len(op_return) > 0 and len(op_return) <= 255:
		payload = OP_RETURN_payload(op_return)
		script = '6a' + binascii.b2a_hex(payload).decode('utf-8', errors='ignore')
		outputs.append({'value' : 0, 'script' : script})

	# creación de transacción
	tx = mktx(inputs, outputs)

	# Firma de cada output
	for i in range(len(inputs)):
		tx = sign(tx, i, privkey)

	broadcasting = post('https://explorer.cha.terahash.cl/api/tx/send', data={'rawtx' : tx})

	return broadcasting

def OP_RETURN_payload(string):
	metadata = bytes(string, 'utf-8')
	metadata_len= len(metadata)
	
	if metadata_len<=75:
		payload=bytearray((metadata_len,))+metadata # length byte + data (https://en.bitcoin.it/wiki/Script)
	elif metadata_len<=256:
		payload=b"\x4c"+bytearray((metadata_len,))+metadata # OP_PUSHDATA1 format
	else:
		payload=b"\x4d"+bytearray((metadata_len%256,))+bytearray((int(metadata_len/256),))+metadata # OP_PUSHDATA2 format

	return payload