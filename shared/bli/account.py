from flask import current_app
from datetime import datetime

from shared.util import logger, error, constants
from shared.db.model import *

LOGGER = logger.getLogger('shared.bli.account')

def __trim_dict(**kwargs):
    return {key: value for key, value in kwargs.items() if value}

def signup(account):
    LOGGER.info('signup entry')

    try:
        existing_account = get_account_by_email(account.email)
    except Exception as e:
        LOGGER.error(e.message)
        raise e

    if existing_account is not None:
        raise error.AccountExistsError(constants.ACCOUNT_WITH_EMAIL_ALREADT_EXISTS)

    try:
        #NOTE: The account parameters are not verified, if it is a non None value then it will be sent as param to the Account model
        current_app.db_session.add(account)
        current_app.db_session.commit()
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)

    #TODO: Send verification email

    LOGGER.info('signup exit')
