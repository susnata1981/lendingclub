from flask import current_app

PHONE_VERIFICATION_MSG = 'Ziplly: your verification code is {0}'
ACCOUNT_NOT_VERIFIED = 'You must verify your phone number first'
INVALID_CREDENTIALS = 'Username or password is invalid'
MISSING_ACCOUNT = 'Missing account information'
UNKNOWN_ERROR = 'Unknown error'
NOT_AVAILABLE = 'Not available'
BANK_ALREADY_ADDED = 'You have already added this bank account'
PLEASE_TRY_AGAIN = 'Sorry, there was an error on the server, please try again.'

SIGNUP_EMAIL_SUBJECT = 'Thanks for expressing interest'
SIGNUP_EMAIL_BODY = '''
<p>
Thanks for expressing interest in Ziplly. We are currently working on building
out the platform and plan on launching soon. You'll be the first to know once our
service is ready. If you've any questions or suggestions in the mean time, we would
love to hear from you.
</p>
<p>
Thanks,<br/>
Sean
</p>
Ziplly (http://www.ziplly.com) making short term borrowing affordable.
'''

def init():
    pass
