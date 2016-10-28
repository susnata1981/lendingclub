from flask import current_app

PHONE_VERIFICATION_MSG = 'Ziplly: your verification code is {0}'
ACCOUNT_NOT_VERIFIED = 'You must verify your phone number first'
INVALID_CREDENTIALS = 'Username or password is invalid'
MISSING_ACCOUNT = 'Missing account information'
UNKNOWN_ERROR = 'Unknown error'
NOT_AVAILABLE = 'Not available'
BANK_ALREADY_ADDED = 'You have already added this bank account'
PLEASE_TRY_AGAIN = 'Sorry, there was an error on the server, please try again.'

FI_ID_KEY = 'fi_id'

SIGNUP_EMAIL_SUBJECT = 'Thanks for expressing interest'
SIGNUP_EMAIL_BODY = '''
<p>
Thanks for expressing interest in Ziplly. We are working on creating the first
membership based lending program that is also affordable. We will contact you as soon
as we are ready to launch.
</p>
<p>
Thanks,<br/>
Admin
</p>
Ziplly (http://www.ziplly.com) making short term borrowing affordable.
'''

def init():
    pass
