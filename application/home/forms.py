import re
from flask_wtf import Form
from wtforms import StringField, IntegerField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import Required, ValidationError, Email

class ContactUsForm(Form):
    name = StringField('name', [Required('Please enter your name')])
    email = StringField('email',
        [Required('Please enter your email'), Email()])
    subject = StringField('subject', validators=[Required('Please enter a subject')])
    message = TextAreaField('message', validators=[Required('Please enter a message')])
    submit = SubmitField('Send')
