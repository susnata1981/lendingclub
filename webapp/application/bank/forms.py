from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, DateTimeField, FloatField, PasswordField, SubmitField, SelectField, BooleanField
from wtforms.validators import Required, ValidationError, Email

class AddRandomDepositForm(FlaskForm):
    name = StringField('account holder name', [Required('Please enter account holder name')])
    country = SelectField('country', choices = [('US', 'United States')], validators = [Required('Please enter the country your bank is located')])
    currency = SelectField('currency', choices = [('usd', 'usd')], validators = [Required('Please enter the currency')])
    routing_number = StringField('routing number', [Required('Please enter your bank routing number')], default = '110000000')
    account_number = StringField('account number', [Required('Please enter your account number')], default = '000123456789')

class VerifyRandomDepositForm(FlaskForm):
    deposit1 = StringField('deposit 1', [Required('Must enter deposit 1')], default="32")
    deposit2 = StringField('deposit 2', [Required('Must enter deposit 2')], default="45")
