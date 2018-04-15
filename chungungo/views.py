from flask import render_template, redirect, url_for, request, session, flash
from chungungo import app
from chungungo.validator import check_bc
from bitcoin import *

@app.route('/')
def home():
	if 'address' in session:
		return render_template('home.html')
	else:
		return redirect(url_for('login'))


@app.route('/login', methods=['get','POST'])
def login():
	if request.method == 'POST':
		address = request.form['address']
		privkey = request.form['privkey']

		verify = check_bc(address)

		if verify and address.startswith('c') and len(privkey) == 52:
			login_addr = privtoaddr(privkey, 88)

			if login_addr == address:
				session['address'] = address
				session['privkey'] = privkey
				return redirect(url_for('home'))

		flash(u'Login error', 'is-danger')

	return render_template('login.html')

@app.route('/logout')
def logout():
	session.pop('address', None)
	session.pop('privkey', None)
	return redirect(url_for('home'))