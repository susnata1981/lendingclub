# Add bank has some issues in Instant Verification
#     1. ISSUE: even if I select 'Other' in the add_bank drop down it is showing 'Instant Verification' option.
#     2. ISSUE: Instant verification : progress as bank gets added not shown, also errors not shown.
#     3. ISSUE: Instant verification: what messaging should we show if a the plaid_account_id is already present for a different user.
#     4. ISSUE: Instant verification: adding different account_type in same user bank account has same access token. need to remove the unique constraint on access_token.
#     5. ISSUE: Instant verification: success transition is not happening.

from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify
from plaid import Client
from shared.services import stripe_client
from shared.db.model import *
from forms import *
import traceback
import random
from datetime import datetime
from flask.ext.login import current_user, login_required, login_user, logout_user
from shared.util import constants, error
from shared import services
from shared.util import util, error
from shared.bli import account as accountBLI
from pprint import pprint
import requests
import json
import logging
import dateutil
from dateutil.relativedelta import relativedelta

bank_bp = Blueprint('bank_bp', __name__, url_prefix='/bank')
RANDOM_DEPOSIT_FI_ID_KEY = 'random_deposit_fi_id'

@bank_bp.route('/add_bank', methods=['GET', 'POST'])
@login_required
def add_bank():
    if request.method == 'GET':
        institutions = get_all_iav_supported_institutions()
        return render_template('bank/add_bank.html',
        institutions = institutions)
    else:
        try:
            public_token = request.form['public_token']
            plaid_account_id = request.form['bank_account_id']
            bank_account_name = request.form['bank_account_name']
            institution = request.form['institution']
            institution_type = request.form['institution_type']

            response = json.loads(plaid_exchange_token(public_token, plaid_account_id))
            result = {}
            if get_fi_by_plaid_account_id(response['account_id']) is not None:
                #TODO: this acocunt id could be present for same user or for different user
                # need to think about what messaging shoud be here.
                result['error'] = True
                result['message'] = constants.BANK_ALREADY_ADDED
                return jsonify(result)

            fi = Fi(
                account_name = bank_account_name,
                plaid_account_id = plaid_account_id,
                institution = institution,
                institution_type = institution_type,
                verification_type = Fi.INSTANT,
                status = Fi.VERIFIED,
                plaid_access_token = response['access_token'],
                stripe_bank_account_token = response['stripe_bank_account_token'],
                primary = accountBLI.need_primary_bank(current_user),
                usage_status = Fi.ACTIVE,
                time_updated = datetime.now(),
                time_created = datetime.now())
            current_user.fis.append(fi)

            logging.info('fetching financial information...')
            fetch_financial_information_from_plaid(fi)
            #TODO: should we save the Fi even if the fetch bank ifo fails? - I think yes,
            # we can retry the fetch bank info later
            logging.info('received financial information...')
            current_app.db_session.add(current_user)
            current_app.db_session.commit()

            response = {}
            response['success'] = True

            return jsonify(response)
        except Exception as e:
            traceback.print_exc()
            logging.error('add_bank::received exception %s' % e)
            response = {}
            response['error'] = 'true'
            return jsonify(response)

@bank_bp.route('/add_random_deposit', methods=['GET', 'POST'])
@login_required
def add_random_deposit():
    form = AddRandomDepositForm(request.form)
    if form.validate_on_submit():
        try:
            response = current_app.stripe_client.add_customer_bank(
                current_user.stripe_customer_id,
                account_number = form.account_number.data,
                routing_number = form.routing_number.data,
                currency = form.currency.data,
                country = form.country.data,
                account_holder_name = form.name.data)
        except error.UserInputError as e:
            flash(e.message)
            return render_template('bank/add_random_deposit.html', form = form)
        except Exception as e:
            #TODO: should we handle if bank already exists for customer?
            logging.error('add_random_deposit::received exception %s' % e)
            flash(constants.GENERIC_ERROR)
            return render_template('bank/add_random_deposit.html', form = form)

        logging.info('Added bank account to stripe resposne = {}'.format(response))
        fi = Fi(
            institution = response['bank_name'],
            account_number_last_4 = response['last4'],
            stripe_bank_account_token = response['id'],
            verification_type = Fi.RANDOM_DEPOSIT,
            status = Fi.UNVERFIED,
            primary = accountBLI.need_primary_bank(current_user),
            usage_status = Fi.ACTIVE,
            time_updated = datetime.now(),
            time_created = datetime.now())
        current_user.fis.append(fi)
        current_app.db_session.add(current_user)
        current_app.db_session.commit()
        session[RANDOM_DEPOSIT_FI_ID_KEY] = fi.id
        return redirect(url_for('.add_bank_random_deposit_success'))
    else:
        return render_template('bank/add_random_deposit.html', form = form)

@bank_bp.route('/verify_random_deposit', methods=['GET', 'POST'])
@login_required
def verify_random_deposit():
    if not RANDOM_DEPOSIT_FI_ID_KEY in session:
        logging.error('verify_random_deposit call doesn\'t contain %s in session. redirecting to dashboard.' % (RANDOM_DEPOSIT_FI_ID_KEY))
        return redirect(url_for('lending_bp.dashboard'))

    form = VerifyRandomDepositForm(request.form)
    if form.validate_on_submit():
        try:
            fi_id = session[RANDOM_DEPOSIT_FI_ID_KEY]
            fi_to_be_verified = None
            for fi in current_user.fis:
                if fi.id == int(fi_id):
                    fi_to_be_verified = fi
                    break

            #TODO: If 'fi_id' not present, raise exception - show error
            #TODO: If the fi is already verified raise exception - show error
            logging.info('About to verify bank account(stripe token) %s, customer id %s deposit1 %s deposit2 %s '
            % (fi_to_be_verified.stripe_bank_account_token, current_user.stripe_customer_id, form.deposit1.data, form.deposit2.data))

            response = current_app.stripe_client.verify_customer_bank(
                current_user.stripe_customer_id,
                fi_to_be_verified.stripe_bank_account_token,
                form.deposit1.data,
                form.deposit2.data)
            logging.info('Verified bank account, response = ',response)
            session.pop(RANDOM_DEPOSIT_FI_ID_KEY, None)
            return mark_bank_as_verified(fi)
        except error.BankAlreadyVerifiedError:
            logging.info('Stripe service raised BankAlreadyVerifiedError. Updating DB to mark bank with id:%s as verified.' % (fi.id))
            return mark_bank_as_verified(fi)
        except error.IncorrectRandomDepositAmountsError as e:
            logging.info('Stripe service raised IncorrectRandomDepositAmountsError')
            flash(e.message)
            return render_template('bank/verify_random_deposit.html', form=form)
        except error.UserInputError as e:
            flash(e.message)
            return render_template('bank/verify_random_deposit.html', form=form)
        except Exception as e:
            logging.error('failed to verify_account_random_deposit, exception %s' % e)
            flash(constants.GENERIC_ERROR)
            return render_template('bank/verify_random_deposit.html', form=form)
    else:
        return render_template('bank/verify_random_deposit.html', form=form)

def mark_bank_as_verified(fi):
    #TODO: raise exception if fi == None
    fi.status = Fi.VERIFIED
    fi.time_updated = datetime.now()
    current_app.db_session.add(fi)
    current_app.db_session.commit()
    #TODO: show success and show loan review page if needed
    #return redirect(url_for('.application_complete'))
    return redirect(url_for('lending_bp.dashboard'))

@bank_bp.route('/verified', methods=['GET'])
@login_required
def verified():
    return redirect(url_for('lending_bp.dashboard'))

@bank_bp.route('/add_bank_random_deposit_success', methods=['GET'])
@login_required
def add_bank_random_deposit_success():
    #session[RANDOM_DEPOSIT_FI_ID_KEY]
    return render_template('bank/add_bank_random_deposit_success.html')

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
        logging.error('Plaid response didn\'t contain the request plaid_account_id:%s' % (plaid_account_id))
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
