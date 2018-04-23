from flask import render_template, redirect, url_for, request, session, flash, Markup
from chungungo import app
from chungungo.validator import check_bc
from chungungo.network import *
from os import urandom

@app.route('/')
def index():
	if 'address' in session:
		balance = getbalance(session['address'])
		return render_template('home.html', balance=balance)
	else:
		return render_template('index.html')

@app.route('/paper')
def paper():
	rand_string = urandom(2048)
	privkey = sha256(rand_string)
	address = privtoaddr(privkey, 88)
	wallet = {'address' : address, 'privkey' : privkey}
	return render_template('wallet.html', wallet=wallet)



@app.route('/history')
def history():
	if 'address' in session:
		history = gethistory(session['address'])
		return render_template('history.html', history=history)
	else:
		return render_template('index.html')


@app.route('/send', methods=['get','POST'])
def send():
	if 'address' in session:
		balance = getbalance(session['address'])

		if request.method == 'POST':
			address = session['address']
			privkey = session['privkey']

			try:
				receptor = request.form['address']
				op_return = request.form['msg']
				amount = float(request.form['amount'])

				verify = check_bc(receptor)

				if not len(op_return) > 0 or len(op_return) <= 255:
					if verify and receptor.startswith('c'):
						unspent = getunspent(address, amount)

						if amount <= unspent['used'] and amount > 0:
							msg = broadcast(session, unspent, amount, receptor, op_return)

							try:
								flash('Transacción enviada', 'is-primary')
							except:
								msg = broadcasting.text
								flash(Markup('ERROR<br>%s' % msg), 'is-danger')
							
							return redirect(url_for('index'))

						else:
							flash('Saldo insuficiente o inválido', 'is-danger')
					else:
						flash('dirección inválida', 'is-danger')
				else:
					flash('Ingresa un mensaje', 'is-danger')
			except ValueError:
				flash('Ingresa valores válidos', 'is-danger')
		
			return redirect(url_for('send'))
		else:
			return render_template('send.html', balance=balance)
	else:
		return redirect(url_for('index'))



@app.route('/login', methods=['get','POST'])
def login():
	if request.method == 'POST':
		privkey = request.form['privkey']

		try:
			address = privtoaddr(privkey, 88)
			session['address'] = address
			session['privkey'] = privkey

		except AssertionError:
			flash('Llave privada erronea', 'is-danger')
	
		return redirect(url_for('index'))

	return render_template('login.html')


@app.route('/logout')
def logout():
	session.pop('address', None)
	session.pop('privkey', None)
	return redirect(url_for('index'))