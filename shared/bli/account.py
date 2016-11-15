from flask import current_app
from datetime import datetime

from shared.util import logger, error, constants
from shared.db.model import *
from shared.services import mail
import random, string

LOGGER = logger.getLogger('shared.bli.account')

def __trim_dict(**kwargs):
    return {key: value for key, value in kwargs.items() if value}

def signup(account):
    LOGGER.info('signup entry')

    try:
        existing_account = get_account_by_email(account.email)
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)

    if existing_account is not None:
        raise error.AccountExistsError(constants.ACCOUNT_WITH_EMAIL_ALREADT_EXISTS)

    try:
        #NOTE: The account parameters are not verified, if it is a non None value then it will be sent as param to the Account model
        current_app.db_session.add(account)
        current_app.db_session.commit()
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)

    #Send verification email
    try:
        initiate_email_verification(account)
    except error.DatabaseError as e:
        Logger.error(e.message)
        raise error.EmailVerificationSendingError(constants.GENERIC_ERROR, e.orig_exp)

    LOGGER.info('signup exit')

def isEmailVerified(account):
    if account and (account.status == int(Account.VERIFIED) or account.status == int(Account.VERIFIED_EMAIL)):
        return True
    return False

def initiate_email_verification(account):
    LOGGER.info('initiate_email_verification entry')
    id = str(account.id + constants.EMAIL_ACCOUNT_ID_CONSTANT)
    print 'TEST id=:%s' % (id)
    token = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(constants.EMAIL_VERIFICATION_TOKEN_LENGTH))
    print 'TEST token=:%s' % (token)
    account.email_verification_token = token

    try:
        #save token to DB
        current_app.db_session.add(account)
        current_app.db_session.commit()
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)

    # send verification email
    link = constants.EMAIL_VERIFICATION_LINK % (id, token)
    text = 'Thanks for signing up with Ziplly.\nPlease click on the below link to verify your email.\n'+link
    html_text = "<h3>Thanks for signing up with Ziplly.</h3><br /><h4>Please click on the below link to verify your email.</h4><br />"+link

    try:
        mail.send(current_app.config['ADMIN_EMAIL'],
            account.email,
            constants.EMAIL_VERIFICATION_SUBJECT,
            text,
            html_text)
    except Exception as e:
        LOGGER.error(e.message)
        raise error.MailServiceError(constants.GENERIC_ERROR,e)

    LOGGER.info('initiate_email_verification exit')

def verify_email(id, token):
    LOGGER.info('verify_email entry')

    account_id = id - constants.EMAIL_ACCOUNT_ID_CONSTANT
    try:
        account = get_account_by_id(account_id)
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)

    if not account:
        raise error.AccountNotFoundError('Invalid verification code.')
    elif account.status == int(Account.VERIFIED) or account.status == int(Account.VERIFIED_EMAIL):
        raise error.AccountEmailAlreadyVerifiedError('Email already verified.')
    elif token != account.email_verification_token:
        raise error.EmailVerificationNotMatchError('Invalid verification code.')
    else:
        try:
            account.status = Account.VERIFIED_EMAIL
            stripe_customer = current_app.stripe_client.create_customer(
            account.email)
            account.stripe_customer_id = stripe_customer['id']
            account.time_updated = datetime.now()
            current_app.db_session.add(account)
            current_app.db_session.commit()
        except Exception as e:
            LOGGER.error(e.message)
            raise error.DatabaseError(constants.GENERIC_ERROR,e)

    LOGGER.info('verify_email exit')
