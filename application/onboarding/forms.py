import re
from flask_wtf import Form
from wtforms import StringField, IntegerField, PasswordField, SubmitField
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
    street1 = StringField('street1', [Required('Please enter your street address')])
    street2 = StringField('street2')
    city = StringField('city', [Required('Please enter your city')])
    state = StringField('state', [Required('Pleae enter your state')])
    postal_code = IntegerField('postal code', [Required('Please enter your postal code')])

class SelectPlanForm(Form):
    plan_id = IntegerField('plan_id', [Required()])

class GetBankVerificationMethods(Form):
    bank_name = StringField('bank_name', [Required('Must enter your bank name')])
