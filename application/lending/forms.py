import re
from flask_wtf import Form
from wtforms import StringField, IntegerField, DateField, DateTimeField, FloatField, PasswordField, SubmitField, SelectField
from wtforms.validators import Required, ValidationError, Email

class RequestMoneyForm(Form):
    requested_amount = FloatField('requested amount', [Required('Please enter an amount')])
