from chungungo import forms, views
from flask import Flask
from flask_qrcode import QRcode
from flask_babel import Babel

app = Flask(__name__)
qrcode = QRcode(app)

app.config.from_pyfile('settings.cfg')
babel = Babel(app)
