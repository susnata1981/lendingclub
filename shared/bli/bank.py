import requests
import json
from plaid import Client
import logging
from pprint import pprint
from shared.util import constants, error, logger
from shared.db.model import *
from flask import current_app
from shared.bli.viewmodel.bank_data import *
from datetime import datetime

LOGGER = logger.getLogger('shared.bli.bank')

def get_fi_by_plaid_account_id(id):
    return current_app.db_session.query(Fi).filter(Fi.plaid_account_id == id).one_or_none()

def get_plaid_fi_for_account(plaid_id, account_id):
    return current_app.db_session.query(Fi).filter(Fi.plaid_account_id == plaid_id, Fi.account_id == account_id).one_or_none()

def plaid_exchange_token(public_token, account_id):
    payload = {
        'client_id':current_app.config['CLIENT_ID'],
        'secret':current_app.config['CLIENT_SECRET'],
        'public_token':public_token,
        'account_id':account_id
    }
    print 'payload ',json.dumps(payload)

    response = requests.post('https://tartan.plaid.com/exchange_token', data=payload)

    print 'response = ',response.text, 'code = ',response.status_code
    if response.status_code == requests.codes.ok:
        return response.text
    else:
        raise Exception('Failed to exchange token')

def get_bank_info_from_plaid(plaid_access_token, plaid_account_id):
    print 'getting bank info from plaid...'
    Client.config({
        'url': 'https://tartan.plaid.com',
        'suppress_http_errors': True
    })
    client = Client(
    client_id=current_app.config['CLIENT_ID'],
    secret=current_app.config['CLIENT_SECRET'],
    access_token=plaid_access_token)

    # print 'response = ',client.auth_get()
    print '***************************** get-bank-info ='
    pprint(client.auth_get())
    response = client.auth_get().json()
    print 'get_bank_info_from_plaid response = ',response

    ai = {}
    for account in response['accounts']:
        if account['_id'] == plaid_account_id:
            ai['available_balance'] = account['balance']['available']
            ai['current_balance'] = account['balance']['current']
            ai['subtype'] = account['subtype']
            ai['subtype_name'] = account['meta']['name']
            ai['account_number_last_4'] = account['meta']['number']
            ai['institution_type'] = account['institution_type']
            return ai
    if not ai:
        LOGGER.error('Plaid response didn\'t contain the request plaid_account_id:%s' % (plaid_account_id))
        raise error.PlaidBankInfoFetchError('Plaid response didn\'t contain the request plaid_account_id:%s' % (plaid_account_id))

def fetch_financial_information_from_plaid(fi):
    #TODO: If 'fi' is None, raise exception
    response = get_bank_info_from_plaid(fi.plaid_access_token, fi.plaid_account_id)
    fi.available_balance = response['available_balance']
    fi.current_balance = response['current_balance']
    fi.subtype = response['subtype']
    fi.subtype_name = response['subtype_name']
    fi.account_number_last_4 = response['account_number_last_4']
    fi.institution_type = response['institution_type']

def mark_bank_as_verified(fi):
    #TODO: raise exception if fi == None
    fi.status = Fi.VERIFIED
    fi.time_updated = datetime.now()
    try:
        current_app.db_session.add(fi)
        current_app.db_session.commit()
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)

def save_instant_verified_bank(fi, plaid_public_token, account):
    test_fi = get_plaid_fi_for_account(fi.plaid_account_id, account.id)
    if test_fi:
        message = 'Bank account(fi_id:%s) with plaid_account_id:%s already present for account:%s' % (test_fi.id, test_fi.plaid_account_id, account.id)
        LOGGER.error(message)
        raise error.BankAlreadyAdded(message)
    # get plaid response
    response = json.loads(plaid_exchange_token(plaid_public_token, fi.plaid_account_id))
    fi.status = Fi.VERIFIED
    fi.plaid_access_token = response['access_token']
    fi.stripe_bank_account_token = response['stripe_bank_account_token']
    fi.time_created = datetime.now()
    fi.time_updated = datetime.now()
    account.fis.append(fi)
    LOGGER.info('fetching financial information...')
    #TODO: should we save the Fi to DB even if the fetch bank info fails? - I think yes,
    # we can retry the fetch bank info later
    fetch_financial_information_from_plaid(fi)
    LOGGER.info('received financial information...')
    try:
        LOGGER.info('Linking stripe token:%s for stripe customer:%s' % (fi.stripe_bank_account_token, account.stripe_customer_id))
        current_app.stripe_client.add_customer_bank(account.stripe_customer_id, fi.stripe_bank_account_token)
        LOGGER.info('Done linking stripe token:%s for stripe customer:%s' % (fi.stripe_bank_account_token, account.stripe_customer_id))
        current_app.db_session.add(account)
        current_app.db_session.commit()
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)

def save_random_deposit_bank(bank, account):
    try:
        response = current_app.stripe_client.add_customer_bank(
            account.stripe_customer_id,
            account_number = bank.account_number,
            routing_number = bank.routing_number,
            currency = bank.currency,
            country = bank.country,
            account_holder_name = bank.holder_name)
    except error.BankAlreadyVerifiedError:
        LOGGER.info('Bank already verified, continuing to set it as verified in DB.')
    except Exception as e:
        LOGGER.error(e.message)
        raise e

    fi = Fi(
        institution = response['bank_name'],
        account_number_last_4 = response['last4'],
        stripe_bank_account_token = response['id'],
        verification_type = bank.verification_type,
        status = bank.status,
        primary = bank.primary,
        usage_status = bank.usage_status,
        time_updated = datetime.now(),
        time_created = datetime.now())

    try:
        account.fis.append(fi)
        current_app.db_session.add(account)
        current_app.db_session.commit()
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)

def verify_random_deposit(bank_deposit, account):

    fi = None
    for fi in account.fis:
        if fi.id == int(bank_deposit.id):
            fi_to_be_verified = fi
            break
    if not fi:
        LOGGER.error('fi id:%s not found' % (bank_deposit.id))
        raise error.BankNotFoundError('fi id:%s not found' % (bank_deposit.id))

    LOGGER.info('About to verify bank account(stripe token) %s, customer id %s deposit1 %s deposit2 %s '
    % (fi.stripe_bank_account_token, account.stripe_customer_id, bank_deposit.deposit1, bank_deposit.deposit2))
    try:
        response = current_app.stripe_client.verify_customer_bank(
            account.stripe_customer_id,
            fi.stripe_bank_account_token,
            bank_deposit.deposit1, bank_deposit.deposit2)
    except error.BankAlreadyVerifiedError:
        LOGGER.info('Stripe service raised BankAlreadyVerifiedError. Updating DB to mark bank with id:%s as verified.' % (fi.id))

    LOGGER.info('Verified bank account, response = %s' % (response))
    mark_bank_as_verified(fi)
