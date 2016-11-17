import re
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, DateTimeField, FloatField, PasswordField, SubmitField, SelectField
from wtforms.validators import Required, ValidationError, Email, EqualTo

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
    employer_name = StringField('employer name', [Required('Please enter your employer name')])
    employer_phone_number = StringField('employer phone number', [Required('Please enter your phone number'), PhoneNumberValidator()])
    street1 = StringField('street1', [Required('Please enter your street address')])
    street2 = StringField('street2')
    city = StringField('city', [Required('Please enter your city')], render_kw={"placeholder": "city"})
    state = StringField('state', [Required('Pleae enter your state')], render_kw={"placeholder": "state"})
    postal_code = IntegerField('postal code', [Required('Please enter your postal code')], render_kw={"placeholder": "postal code"})
    submit = SubmitField('next')

class ResetPasswordForm(FlaskForm):
    email = StringField('email',[Required('Please enter your email address to recieve the reset password link.'), Email()])
    submit = SubmitField('Reset')

class ResetPasswordConfirmForm(FlaskForm):
    password = PasswordField('password', validators=[Required('Please enter a password'), EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField('re-enter password', validators=[Required('Please re-enter the password')])
    submit = SubmitField('Submit')

class LoanApplicationForm(FlaskForm):
    loan_request_reason = SelectField('borrow-to',
        choices = [('repair-my-car', 'Repair my car'), ('pay-for-medical-bills', 'Pay for my medican bills'),
        ('pay-off-payday-loan', 'Pay off Payday loan')], validators = [Required('Please enter why you would like to borrow')])

    loan_duration = IntegerField('loan duration', [Required('Please enter the duration of your loan')])
    requested_amount = FloatField('requested amount', [Required('Please enter an amount')])

class MakePaymentForm(FlaskForm):
    payment_amount = FloatField('payment amount', [Required('Please enter an amount')])
