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
Thanks for expressing interest in Ziplly. We are working on a newer version
of the ebook "5 Proven Tips For Saving Money On Your Loan".
We will be emailing it to you shortly. Sorry for the delay.
</p>
<p>
Ziplly Admin
</p>
Ziplly (http://www.ziplly.com) short term borrowing made affordable.
'''

DAYS_FOR_DUE_DATE = 30
YOU_OWE_MESSAGE = 'You currently owe ${0} before {1}'
MAX_BORROW_MESSAGE = 'As per your membership plan, the maximum you can borrow is ${0}'
ACCOUNT_ACTIVE_FOR_REQUEST_MONEY_MESSAGE = 'Your account needs to be active to request money.'
ACTIVE_PLAN_REQUIRED_MESSAGE = 'You should be enrolled in a plan to be able to request money.'

def init():
    pass
