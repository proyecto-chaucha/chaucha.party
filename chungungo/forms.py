from flask import flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError

def flash_errors(form):
	for field, errors in form.errors.items():
		for error in errors:
			flash(u"%s - %s" % (getattr(form,field).label.text, error), 'is-danger')

class privkeyform(FlaskForm):
	privkey = PasswordField('Llave privada', validators=[DataRequired()])

class sendform(FlaskForm):
	address = StringField('Dirección', validators=[DataRequired()])
	amount = FloatField('Monto', validators=[DataRequired(), NumberRange(0.001)])
	msg = StringField('Mensaje', validators=[DataRequired(), Length(1,255)])