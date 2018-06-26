from flask import render_template, redirect, url_for, request, \
                  session, flash, Markup
from flask_babel import gettext
from chungungo.validator import *
from chungungo.network import *
from chungungo.forms import *
from chungungo.params import *
from chungungo import app
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'address' in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def flash_tx(msg_raw):
    print(msg_raw.text)
    try:
        msg = msg_raw.json()
        flash(Markup('Transacción enviada exitosamente<br>'
                     + msg['txid']), 'is-primary')
    except:
        msg = msg_raw.text
        flash(Markup('Error de transmisión<br>'
                     + msg), 'is-danger')

@app.route('/')
@login_required
def index():
    balance = getbalance(session['address'])
    return render_template('home.html', balance=balance)

@app.route('/hodl/create', methods=['GET','POST'])
@login_required
def hodlcreate():
    form = hodlcreateform(request.form)
    if form.validate_on_submit():
        locktime = int(request.form['locktime'])
        if locktime > 0:
            privkey = session['privkey']
            script = getRedeemScript(locktime, privkey)
            return render_template('hodlsuccess.html',
                                    script=script,
                                    locktime=locktime)
        flash('Locktime - Error de formato', 'is-danger')
    return render_template('hodlcreate.html', form=form)

@app.route('/hodl/spend', methods=['GET','POST'])
@login_required
def hodlspend():
    form = hodlspendform(request.form)
    if form.validate_on_submit():
        script = request.form['script']
        receptor = request.form['address']

        script_addr = getScriptAddr(script)
        check_locktime = checklocktime(script)

        if check_locktime:
            balance = getbalance(script_addr)
            unspent = getunspent(script_addr, balance)
            if balance > 0:
                args = [script, session, receptor, unspent, balance]
                tx = hodlspendtx(args)
                msg_raw = broadcast(tx)
                flash_tx(msg_raw)
            else:
                flash('Script - Dirección OP_HODL sin saldo', 'is-danger')
        else:
            flash('Script - Locktime menor a tamaño de blockchain', 'is-danger')
    return render_template('hodlspend.html', form=form)

@app.route('/paper')
def paper():
    privkey = encode_privkey(random_key(), 'wif', magic)
    address = privtoaddr(privkey, magic)
    wallet = {'address' : address, 'privkey' : privkey}
    return render_template('wallet.html', wallet=wallet)

@app.route('/history')
@login_required
def history():
    if request.args.get('page'):
        current_page = int(request.args.get('page')) - 1
    else:
        current_page = 0

    history, pages = gethistory(session['address'], current_page)

    return render_template('history.html',
                            history=history,
                            pages=pages,
                            current_page=current_page)

@app.route('/send', methods=['GET','POST'])
@login_required
def send():
    form = sendform(request.form)

    balance = getunspent(session['address'])
    if balance == False:
        flash('Error de lectura de saldo, intenta más tarde', 'is-danger')
        return redirect(url_for('index'))

    if form.validate_on_submit():
        receptor = request.form['address']
        op_return = request.form['msg']
        amount = round(float(request.form['amount']), 8)

        if check_bc(receptor):
            unspent = getunspent(session['address'], amount)

            if amount <= unspent['used']:
                args = [session, unspent, amount, receptor, op_return]
                tx = maketx(args)
                msg_raw = broadcast(tx)
                flash_tx(msg_raw)

                return redirect(url_for('index'))

            else:
                flash('Saldo insuficiente', 'is-danger')
        else:
            flash('Dirección - Error de formato', 'is-danger')

        return redirect(url_for('send'))
    else:
        flash_errors(form)
        return render_template('send.html', balance=balance, form=form)


@app.route('/login', methods=['GET','POST'])
def login():
    form = privkeyform(request.form)
    if form.validate_on_submit():
        privkey = form.privkey.data

        try:
            address = privtoaddr(privkey, magic)
            session['address'] = address
            session['privkey'] = privkey
            return redirect(url_for('index'))

        except:
            flash('Llave Privada - Error de formato', 'is-danger')
    else:
        flash_errors(form)
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('address', None)
    session.pop('privkey', None)
    return redirect(url_for('index'))
