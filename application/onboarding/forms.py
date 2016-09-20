import re
from flask_wtf import Form
from wtforms import StringField, IntegerField, DateField, FloatField, PasswordField, SubmitField, SelectField
from wtforms.validators import Required, ValidationError, Email

class PhoneNumberValidator:
    patt = re.compile('\d{3}-\d{3}-\d{4}')
    message = 'Invalid phone number format (xxx-xxx-xxxx)'

    def __call__(self, form, field):
        pn = field.data
        if not PhoneNumberValidator.patt.match(pn):
            raise ValidationError(PhoneNumberValidator.message)

def SSNValidator():
    message = 'Invalid SSN format (xxx-xxx-xxxx)'
    ssn_pattern = re.compile('\d{3}-\d{3}-\d{4}')

    def validator(form, field):
        if not ssn_pattern.match(field.data):
            raise ValidationError(message)
    return validator

class SignupForm(Form):
    first_name = StringField('firstname', [Required('Please enter your firstname')])
    last_name = StringField('lastname', [Required('Please enter your lastname')])
    phone_number = StringField('phone number',
        [Required('Please enter your phone number'), PhoneNumberValidator()])
    password = PasswordField('password', validators=[Required('Please enter a password')])
    submit = SubmitField('Signup')

class LoginForm(Form):
    phone_number = StringField('phone number', [Required('Phone number must be provided')])
    password = PasswordField('password', [Required('Password must be provided')])
    submit = SubmitField('Login')

class PhoneVerificationForm(Form):
    verification_code = IntegerField('verification code', [Required('Please enter the verification code')])
    submit = SubmitField('Verify')

class PersonalInformationForm(Form):
    email = StringField('email', [Required('Please enter your email'), Email()])
    ssn = StringField('social security', [Required('Please enter your social security'), SSNValidator()])
    dob = DateField('date of birth', [Required('Please enter your date of birth')], format="%m/%d/%Y")
    driver_license_number = StringField('driver license number',
    [Required('Please enter your driver license number')])
    street1 = StringField('street1', [Required('Please enter your street address')])
    street2 = StringField('street2')
    city = StringField('city', [Required('Please enter your city')])
    state = StringField('state', [Required('Pleae enter your state')])
    postal_code = IntegerField('postal code', [Required('Please enter your postal code')])


class EmployerInformationForm(Form):
    employer_name = StringField('* employer name', [Required('Please enter your employer name')])
    employer_phone_number = StringField('* employer phone number', [Required('Please enter your phone number'), PhoneNumberValidator()])
    employer_street1 = StringField('* street1', [Required('Please enter your street address')])
    employer_street2 = StringField('street2')
    employer_city = StringField('* city', [Required('Please enter your city')])
    employer_state = StringField('* state', [Required('Pleae enter your state')])
    employer_postal_code = IntegerField('* postal code', [Required('Please enter your postal code')])
    submit = SubmitField('next')


class SelectPlanForm(Form):
    plan_id = IntegerField('plan_id', [Required()])

class GetBankVerificationMethods(Form):
    bank_name = StringField('bank_name', [Required('Must enter your bank name')])

class RandomDepositForm(Form):
    name = StringField('account holder name', [Required('Please enter account holder name')])
    country = SelectField('country', choices = [('US', 'United States')], validators = [Required('Please enter the country your bank is located')])
    currency = SelectField('currency', choices = [('usd', 'usd')], validators = [Required('Please enter the currency')])
    routing_number = StringField('routing number', [Required('Please enter your bank routing number')])
    account_number = StringField('account number', [Required('Please enter your account number')])

class RandomDepositVerifyAccountForm(Form):
    deposit1 = StringField('deposit 1', [Required('Must enter deposit 1')])
    deposit2 = StringField('deposit 2', [Required('Must enter deposit 2')])
