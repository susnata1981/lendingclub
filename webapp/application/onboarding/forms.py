import re
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, DateTimeField, FloatField, PasswordField, SubmitField, SelectField, BooleanField
from wtforms.validators import Required, ValidationError, Email

class PhoneNumberValidator:
    patt = re.compile('\d{3}-\d{3}-\d{4}')
    message = 'Invalid phone number format (xxx-xxx-xxxx)'

    def __call__(self, form, field):
        pn = field.data
        if not PhoneNumberValidator.patt.match(pn):
            raise ValidationError(PhoneNumberValidator.message)

def SSNValidator():
    message = 'Invalid SSN format (xxx-xx-xxxx)'
    ssn_pattern = re.compile('\d{3}-\d{2}-\d{4}')

    def validator(form, field):
        if not ssn_pattern.match(field.data):
            raise ValidationError(message)
    return validator

class SignupForm(FlaskForm):
    first_name = StringField('first_name', [Required('Please enter your firstname')], render_kw={"placeholder": "firstname"})
    last_name = StringField('lastname', [Required('Please enter your lastname')], render_kw={"placeholder": "lastname"})
    street1 = StringField('street1', [Required('Please enter your street address')])
    street2 = StringField('street2')
    city = StringField('city', [Required('Please enter your city')], render_kw={"placeholder": "city"})
    state = StringField('state', [Required('Pleae enter your state')], render_kw={"placeholder": "state"})
    postal_code = IntegerField('postal code', [Required('Please enter your postal code')], render_kw={"placeholder": "postal code"})
    ssn = StringField('social security', [Required('Please enter your social security'), SSNValidator()])
    dob = DateTimeField('date of birth (mm/dd/yyyy)', [Required('Please enter your date of birth')], format="%m/%d/%Y")
    # driver_license_number = StringField('driver license number',
    # [Required('Please enter your driver license number')])
    phone_number = StringField('phone number',
        [Required('Please enter your phone number'), PhoneNumberValidator()])
    promotion_code = StringField('promotion code')
    email = StringField('email', [Required('Please enter your email'), Email()])
    password = PasswordField('password', validators=[Required('Please enter a password')])
    consent = BooleanField('I consent', default=False)
    submit = SubmitField('Signup')

class LoginForm(FlaskForm):
    email = StringField('email', [Required('Please enter your email'), Email()])
    password = PasswordField('password', [Required('Password must be provided')])
    submit = SubmitField('Login')

class PhoneVerificationForm(FlaskForm):
    verification_code = IntegerField('enter verification code', [Required('Please enter the verification code')], default = 1111)
    submit = SubmitField('Verify')

class ResendEmailVerificationForm(FlaskForm):
    email = StringField('*email',[Required('Please enter your email address to recieve the verification email.'), Email()])
    submit = SubmitField('Resend')

class EmployerInformationForm(FlaskForm):
    employer_name = StringField('employer name', [Required('Please enter your employer name')])
    employer_phone_number = StringField('* employer phone number', [Required('Please enter your phone number'), PhoneNumberValidator()])
    street1 = StringField('street1', [Required('Please enter your street address')])
    street2 = StringField('street2')
    city = StringField('city', [Required('Please enter your city')])
    state = StringField('state', [Required('Pleae enter your state')])
    postal_code = IntegerField('postal code', [Required('Please enter your postal code')])
    submit = SubmitField('next')

class GetBankVerificationMethods(FlaskForm):
    bank_name = StringField('bank_name', [Required('Must enter your bank name')])

class AddRandomDepositForm(FlaskForm):
    name = StringField('account holder name', [Required('Please enter account holder name')])
    country = SelectField('country', choices = [('US', 'United States')], validators = [Required('Please enter the country your bank is located')])
    currency = SelectField('currency', choices = [('usd', 'usd')], validators = [Required('Please enter the currency')])
    routing_number = StringField('routing number', [Required('Please enter your bank routing number')], default = '110000000')
    account_number = StringField('account number', [Required('Please enter your account number')], default = '000123456789')

class VerifyRandomDepositForm(FlaskForm):
    deposit1 = StringField('deposit 1', [Required('Must enter deposit 1')], default="32")
    deposit2 = StringField('deposit 2', [Required('Must enter deposit 2')], default="45")
    
