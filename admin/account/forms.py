from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, DateField, DateTimeField
from wtforms.validators import Required, ValidationError, Email, EqualTo
from shared.util import util

class LoginForm(FlaskForm):
    email = StringField('email', [Required('Please enter your email'), Email()])
    password = PasswordField('password', [Required('Password must be provided')])
    submit = SubmitField('Login')
