from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import Required, ValidationError, Email, EqualTo

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
