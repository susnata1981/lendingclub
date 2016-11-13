from flask import current_app

PHONE_VERIFICATION_MSG = 'Ziplly: your verification code is {0}'
ACCOUNT_NOT_VERIFIED = 'You must verify your phone number first'
INVALID_CREDENTIALS = 'Username or password is invalid'
MISSING_ACCOUNT = 'Missing account information'
UNKNOWN_ERROR = 'Unknown error'
NOT_AVAILABLE = 'Not available'
BANK_ALREADY_ADDED = 'You have already added this bank account'
PLEASE_TRY_AGAIN = 'Sorry, there was an error on the server, please try again.'
GENERIC_ERROR = 'Aww crap....something bad happened. Please try again after sometime.'
ACCOUNT_WITH_EMAIL_ALREADT_EXISTS = 'Account with this email already exists'

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
EXTENSION_DUE_DATE = 30
MAX_EXTENSIONS_ALLOWED = 3
YOU_OWE_MESSAGE = 'You currently owe ${0} before {1}'
MAX_BORROW_MESSAGE = 'As per your membership plan, the maximum you can borrow is ${0}'
ACCOUNT_ACTIVE_FOR_REQUEST_MONEY_MESSAGE = 'Your account needs to be active to request money.'
ACTIVE_PLAN_REQUIRED_MESSAGE = 'You should be enrolled in a plan to be able to request money.'

#Email verification constants
EMAIL_ACCOUNT_ID_CONSTANT = 458213
EMAIL_VERIFICATION_TOKEN_NAME = 'tok'
EMAIL_VERIFICATION_TOKEN_LENGTH = 12
EMAIL_VERIFICATION_LINK = 'http://localhost:8080/account/%s/verify?' + EMAIL_VERIFICATION_TOKEN_NAME + '=%s'
EMAIL_VERIFICATION_SUBJECT = 'Verify your email to complete your signup'
EMAIL_VERIFICATION_SEND_FAILURE_MESSAGE = 'Sorry, our service failed to send the verification email. Please request the verification email again.'
ACCOUNT_CREATED_BUT_EMAIL_VERIFICATION_SEND_FAILURE_MESSAGE = 'Account successfully created but our service failed to send the verification email. Please request the verification email again.'


def init():
    pass
