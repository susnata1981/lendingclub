from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify
from plaid import Client
from shared.services import stripe_client
from forms import *
from shared.db.model import *
import traceback
import random
from datetime import datetime
from flask.ext.login import current_user, login_required, login_user, logout_user
from shared.util import constants, error
from shared import services
from shared.bli import account as accountBLI
from pprint import pprint
import requests
import json
import logging
import dateutil
from dateutil.relativedelta import relativedelta
from shared.bli.viewmodel.notification import Notification
from shared.bli import bank as bankBLI


account_bp = Blueprint('account_bp', __name__, url_prefix='/account')

def generate_and_store_new_verification_code(account):
    # verification_code = random.randint(1000, 9999)
    verification_code = 1111
    account.phone_verification_code = verification_code
    current_app.db_session.add(account)
    current_app.db_session.commit()
    return verification_code

@account_bp.route('/verify/resend', methods=['GET', 'POST'])
def resend_email_verification():
    form = ResendEmailVerificationForm(request.form)
    data = {}
    if form.validate_on_submit():
        email = form.email.data
        try:
            account = get_account_by_email(email)
            if not account:
                flash('Account for this email(%s) doesn\'t exist at Ziplly.' % (email))
                data['show_email_verification_form'] = True
            elif accountBLI.is_email_verified(account):
                flash('Email already verified.')
                data['email_already_verified'] = True
            else:
                try:
                    accountBLI.initiate_email_verification(account)
                    data['email_sent'] = True
                except error.EmailVerificationSendingError:
                    flash(constants.EMAIL_VERIFICATION_SEND_FAILURE_MESSAGE)
                    data['show_email_verification_form'] = True
        except Exception:
            flash(constants.GENERIC_ERROR)

            data['show_email_verification_form'] = True
    else:
        data['show_email_verification_form'] = True
    return render_template('onboarding/verify_email.html', data=data, form=form)

@account_bp.route('/<id>/verify', methods=['GET'])
def verify_email(id):
    form = ResendEmailVerificationForm(request.form)
    token = request.args.get(constants.VERIFICATION_TOKEN_NAME)
    data = {}
    try:
        accountBLI.verify_email(int(id), token)
        return redirect(url_for('account_bp.account_verified'))
    except (error.AccountNotFoundError, error.EmailVerificationNotMatchError) as e:
        flash('Invalid verification code.')
        data['show_email_verification_form'] = True
    except error.AccountEmailAlreadyVerifiedError:
        flash('Email already verified.')
        data['email_already_verified'] = True
    except error.DatabaseError:
        flash(constants.GENERIC_ERROR)
        data['show_email_verification_form'] = True
    return render_template('onboarding/verify_email.html', data=data, form=form)

@account_bp.route('/verify', methods=['GET', 'POST'])
def verify_phone_number():
    form = PhoneVerificationForm(request.form)
    if form.validate_on_submit():
        account = get_account_by_id(session['account_id'])
        if account.status == int(Account.UNVERIFIED) and \
        form.verification_code.data == account.phone_verification_code:
            account.status = Account.VERIFIED_PHONE

            stripe_customer = current_app.stripe_client.create_customer(
            account.phone_number)

            account.stripe_customer_id = stripe_customer['id']
            account.time_updated = datetime.now()
            current_app.db_session.add(account)
            current_app.db_session.commit()
            return redirect(url_for('account_bp.account_verified'))
        else:
            flash('Invalid verification code')
    return render_template('onboarding/verify_phone.html', form=form)

@account_bp.route('/account_verified', methods=['GET'])
def account_verified():
    return render_template('onboarding/account_verified.html')

# ajax
@account_bp.route('/resend_verification', methods=['POST'])
def resend_verification():
    if session['account_id'] is None:
        return jsonify({
            'error': True,
            'description': constants.MISSING_ACCOUNT
        })
    try:
        account = get_account_by_id(session['account_id'])
        verification_code = generate_and_store_new_verification_code(account)
        target_phone = '+1' + account.phone_number
        # services.phone.send_message(target_phone, constants.PHONE_VERIFICATION_MSG.format(verification_code))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({
            'error': True,
            'description': traceback.print_exc()
        })

@account_bp.route('/', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('.account'))

    form = SignupForm(request.form)
    print 'errors - ',form.errors
    if form.validate_on_submit():
        try:
            now = datetime.now()
            account = Account(
               first_name = form.first_name.data,
               last_name = form.last_name.data,
               phone_number = form.phone_number.data,
               email = form.email.data,
               dob = form.dob.data,
               ssn = form.ssn.data,
               promotion_code = form.promotion_code.data,
               password = form.password.data,
               time_created = now,
               time_updated = now)

            address = Address(
                street1 = form.street1.data,
                street2 = form.street2.data,
                city = form.city.data,
                state = form.state.data,
                postal_code = form.postal_code.data,
                address_type = Address.EMPLOYER,
               time_created = now,
               time_updated = now)

            account.addresses.append(address)

            accountBLI.signup(account)
        except error.AccountExistsError:
            flash(constants.ACCOUNT_WITH_EMAIL_ALREADT_EXISTS)
            return render_template('onboarding/signup.html', form=form)
        except error.EmailVerificationSendingError:
            flash(constants.ACCOUNT_CREATED_BUT_EMAIL_VERIFICATION_SEND_FAILURE_MESSAGE)
            data = {}
            data['show_email_verification_form'] = True
            email_form = ResendEmailVerificationForm(request.form)
            return render_template('onboarding/verify_email.html', data=data, form=email_form)
        except error.DatabaseError as de:
            print 'ERROR: Database Exception: %s' % (de.message)
            flash(constants.GENERIC_ERROR)
            return render_template('onboarding/signup.html', form=form)
        except Exception as e:
            print 'ERROR: General Exception: %s' % (e.message)
            flash(constants.GENERIC_ERROR)
            return render_template('onboarding/signup.html', form=form)

        # verify email message
        data = {}
        data['email_sent'] = True
        email_form = ResendEmailVerificationForm(request.form)
        return render_template('onboarding/verify_email.html', data=data, form=email_form)

    return render_template('onboarding/signup.html', form=form)


@account_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        try:
            account = accountBLI.verify_login(form.email.data, form.password.data)
            login_user(account)
            next = request.args.get('next')
            # next_is_valid should check if the user has valid
            # permission to access the `next` url
            # print 'Next page =',next,' is_valid_next =',next_is_valid(next)
            # if not next_is_valid(next):
            #     return flask.abort(404)
            return redirect(next or url_for('lending_bp.dashboard'))
        except error.DatabaseError as de:
            print 'Database error:',de.orig_exp.message
            flash(constants.GENERIC_ERROR)
            return render_template('account/login.html', form=form)
        except error.InvalidLoginCredentialsError:
            # print 'Invalid credentials'
            flash(constants.INVALID_CREDENTIALS)
            return render_template('account/login.html', form=form)
        except error.EmailVerificationRequiredError:
            # print 'Email verification required'
            flash(constants.ACCOUNT_NOT_VERIFIED)
            # verify email message
            data = {}
            data['email_verification_required'] = True
            email_form = ResendEmailVerificationForm(request.form)
            return render_template('onboarding/verify_email.html', data=data, form=email_form)
        except Exception as e:
            print 'Exception::',e
            print traceback.format_exc()
            return render_template('404.html')
    return render_template('account/login.html', form=form)

@account_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('.login'))

@account_bp.route('/profile', methods=['GET'])
@login_required
def account():
    return render_template('account/account.html')

@account_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_account():
    form = EditProfileForm(request.form)
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        # addr = get_current_address()
        # if addr:
        current_user.addresses[0].street1 = form.street1.data
        current_user.addresses[0].street2 = form.street2.data
        current_user.addresses[0].city = form.city.data
        current_user.addresses[0].state = form.state.data
        current_user.addresses[0].postal_code = form.postal_code.data
        current_user.dob = form.dob.data
        current_user.ssn = form.ssn.data
        current_user.phone_number = form.phone_number.data
        current_user.email = form.email.data

        # current_app.db_session.update(current_user)
        print "****************************************"
        pprint(current_user.addresses[0])
        # current_app.db_session.add(current_user.addresses[0])
        current_app.db_session.commit()

        notifiation = Notification(
        title = 'Your account has been updated.',
        notification_type = Notification.SUCCESS)
        flash(notifiation.to_map())
        return redirect(url_for('.account'))
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        addr = get_current_address()
        if addr:
            form.street1.data = addr.street1
            form.street2.data = addr.street2
            form.city.data = addr.city
            form.state.data = addr.state
            form.postal_code.data = addr.postal_code
            form.dob.data = datetime.strptime(current_user.dob, "%Y-%m-%d %H:%M:%S")
            form.ssn.data = current_user.ssn
            form.phone_number.data = current_user.phone_number
            form.email.data = current_user.email
    return render_template('account/edit_profile.html', form=form)

@account_bp.route('/add_bank', methods=['GET', 'POST'])
@login_required
def add_bank():
    if request.method == 'GET':
        institutions = get_all_iav_supported_institutions()
        return render_template('onboarding/add_bank.html',
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
            #TODO: should we save the Fi to DB even if the fetch bank info fails? - I think yes,
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


#TODO handle duplicate bank addition.
@account_bp.route('/add_random_deposit', methods=['GET', 'POST'])
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
            return render_template('onboarding/add_random_deposit.html', form = form)
        except Exception as e:
            #TODO: should we handle if bank already exists for customer?
            logging.error('add_random_deposit::received exception %s' % e)
            flash(constants.GENERIC_ERROR)
            return render_template('onboarding/add_random_deposit.html', form = form)

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
        return redirect(url_for('.add_bank_random_deposit_success'))
    else:
        return render_template('onboarding/add_random_deposit.html', form = form)

@account_bp.route('/start_random_deposit_verification', methods=['POST'])
@login_required
def start_random_deposit_verification():
    fi_id = request.form.get('fi_id')
    if fi_id:
        session[bankBLI.RANDOM_DEPOSIT_FI_ID_KEY] = fi_id
        return redirect(url_for('.verify_random_deposit'))
    flash('error')
    return redirect(url_for('lending_bp.dashboard'))

@account_bp.route('/verify_random_deposit', methods=['GET', 'POST'])
@login_required
def verify_random_deposit():
    if not bankBLI.RANDOM_DEPOSIT_FI_ID_KEY in session:
        logging.error('verify_random_deposit call doesn\'t contain %s in session. redirecting to dashboard.' % (bankBLI.RANDOM_DEPOSIT_FI_ID_KEY))
        return redirect(url_for('lending_bp.dashboard'))

    form = VerifyRandomDepositForm(request.form)
    if form.validate_on_submit():
        try:
            fi_id = session[bankBLI.RANDOM_DEPOSIT_FI_ID_KEY]
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
            session.pop(bankBLI.RANDOM_DEPOSIT_FI_ID_KEY, None)
            return mark_bank_as_verified(fi)
        except error.BankAlreadyVerifiedError:
            logging.info('Stripe service raised BankAlreadyVerifiedError. Updating DB to mark bank with id:%s as verified.' % (fi.id))
            return mark_bank_as_verified(fi)
        except error.IncorrectRandomDepositAmountsError as e:
            logging.info('Stripe service raised IncorrectRandomDepositAmountsError')
            flash(e.message)
            return render_template('onboarding/verify_random_deposit.html', form=form)
        except error.UserInputError as e:
            flash(e.message)
            return render_template('onboarding/verify_random_deposit.html', form=form)
        except Exception as e:
            logging.error('failed to verify_account_random_deposit, exception %s' % e)
            flash(constants.GENERIC_ERROR)
            return render_template('onboarding/verify_random_deposit.html', form=form)
    else:
        return render_template('onboarding/verify_random_deposit.html', form=form)

@account_bp.route('/verified', methods=['GET'])
@login_required
def verified():
    return redirect(url_for('lending_bp.dashboard'))

@account_bp.route('/add_bank_random_deposit_success', methods=['GET'])
@login_required
def add_bank_random_deposit_success():
    return render_template('onboarding/add_bank_random_deposit_success.html')

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

def mark_bank_as_verified(fi):
    #TODO: raise exception if fi == None
    fi.status = Fi.VERIFIED
    fi.time_updated = datetime.now()
    current_app.db_session.add(fi)
    current_app.db_session.commit()
    #TODO: show success and show loan review page if needed
    #return redirect(url_for('.application_complete'))
    return redirect(url_for('lending_bp.dashboard'))

def get_current_address():
    if current_user.addresses:
        return current_user.addresses[0]
    return None
