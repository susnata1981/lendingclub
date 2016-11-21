from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, DateField, DateTimeField
from wtforms.validators import Required, ValidationError, Email, EqualTo
from shared.util import util
from shared.util.util import PhoneNumberValidator

class LoginForm(FlaskForm):
    email = StringField('email', [Required('Please enter your email'), Email()])
    password = PasswordField('password', [Required('Password must be provided')])
    submit = SubmitField('Login')

class ResetPasswordForm(FlaskForm):
    email = StringField('email',[Required('Please enter your email address to recieve the reset password link.'), Email()])
    submit = SubmitField('Reset')

class ResetPasswordConfirmForm(FlaskForm):
    password = PasswordField('password', validators=[Required('Please enter a password'), EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField('re-enter password', validators=[Required('Please re-enter the password')])
    submit = SubmitField('Submit')

class EditProfileForm(FlaskForm):
    first_name = StringField('first_name', [Required('Please enter your firstname')], render_kw={"placeholder": "firstname"})
    last_name = StringField('lastname', [Required('Please enter your lastname')], render_kw={"placeholder": "lastname"})
    street1 = StringField('street1', [Required('Please enter your street address')])
    street2 = StringField('street2')
    city = StringField('city', [Required('Please enter your city')], render_kw={"placeholder": "city"})
    state = StringField('state', [Required('Pleae enter your state')], render_kw={"placeholder": "state"})
    postal_code = IntegerField('postal code', [Required('Please enter your postal code')], render_kw={"placeholder": "postal code"})
    ssn = StringField('social security', [Required('Please enter your social security'), util.SSNValidator()])
    dob = DateTimeField('date of birth (mm/dd/yyyy)', [Required('Please enter your date of birth')], format="%m/%d/%Y")
    phone_number = StringField('phone number',
        [Required('Please enter your phone number'), PhoneNumberValidator()])
    email = StringField('email', [Required('Please enter your email'), Email()])
    submit = SubmitField('Update')
