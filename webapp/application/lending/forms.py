from flask_wtf import FlaskForm
from wtforms import IntegerField, FloatField, SelectField
from wtforms.validators import Required, ValidationError

class LoanApplicationForm(FlaskForm):
    loan_request_reason = SelectField('borrow-to',
        choices = [('repair-my-car', 'Repair my car'), ('pay-for-medical-bills', 'Pay for my medican bills'),
        ('pay-off-payday-loan', 'Pay off Payday loan')], validators = [Required('Please enter why you would like to borrow')])

    loan_duration = IntegerField('loan duration', [Required('Please enter the duration of your loan')])
    requested_amount = FloatField('requested amount', [Required('Please enter an amount')])

class MakePaymentForm(FlaskForm):
    payment_amount = FloatField('payment amount', [Required('Please enter an amount')])
