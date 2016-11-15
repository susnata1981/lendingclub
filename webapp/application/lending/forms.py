import re
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, DateTimeField, FloatField, PasswordField, SubmitField, SelectField
from wtforms.validators import Required, ValidationError, Email

class PhoneNumberValidator:
    patt = re.compile('\d{3}-\d{3}-\d{4}')
    message = 'Invalid phone number format (xxx-xxx-xxxx)'

    def __call__(self, form, field):
        pn = field.data
        if not PhoneNumberValidator.patt.match(pn):
            raise ValidationError(PhoneNumberValidator.message)

class EmployerInformationForm(FlaskForm):
    employment_type = SelectField('employment type',
        choices = [('full-time', 'Full Time'), ('part-time', 'Part Time'), ('self-employed', 'Self Employed'), ('unemployed', 'Unemployed')], validators = [Required('Please enter your employment type')])
    employer_name = StringField('* employer name', [Required('Please enter your employer name')])
    employer_phone_number = StringField('* employer phone number', [Required('Please enter your phone number'), PhoneNumberValidator()])
    street1 = StringField('* street1', [Required('Please enter your street address')])
    street2 = StringField('street2')
    city = StringField('* city', [Required('Please enter your city')])
    state = StringField('* state', [Required('Pleae enter your state')])
    postal_code = IntegerField('* postal code', [Required('Please enter your postal code')])
    submit = SubmitField('next')

class RequestMoneyForm(FlaskForm):
    requested_amount = FloatField('requested amount', [Required('Please enter an amount')])

class MakePaymentForm(FlaskForm):
    payment_amount = FloatField('payment amount', [Required('Please enter an amount')])
