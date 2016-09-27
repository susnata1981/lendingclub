from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify
from plaid import Client
from application.services import stripe_client
from forms import *
from application.db.model import *
import traceback
import random
from datetime import datetime
from flask.ext.login import current_user, login_required, login_user, logout_user
from application.util import constants
from application import services, common
from pprint import pprint
import requests
import json
import logging

onboarding_bp = Blueprint('onboarding_bp', __name__, url_prefix='/account')

def generate_and_store_new_verification_code(account):
    verification_code = random.randint(1000, 9999)
    account.phone_verification_code = verification_code
    current_app.db_session.add(account)
    current_app.db_session.commit()
    return verification_code

@onboarding_bp.route('/verify', methods=['GET', 'POST'])
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
            return redirect(url_for('onboarding_bp.account_verified'))
        else:
            flash('Invalid verification code')
    return render_template('onboarding/verify.html', form=form)

@onboarding_bp.route('/account_verified', methods=['GET'])
def account_verified():
    return render_template('onboarding/account_verified.html')

# ajax
@onboarding_bp.route('/resend_verification', methods=['POST'])
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
        services.phone.send_message(target_phone, constants.PHONE_VERIFICATION_MSG.format(verification_code))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({
            'error': True,
            'description': traceback.print_exc()
        })

@onboarding_bp.route('/', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('.account'))

    form = SignupForm(request.form)
    if form.validate_on_submit():
        existing_account = get_account_by_phone_number(form.phone_number.data)
        if existing_account is not None:
            flash('Account with this phone number already exists')
            return render_template('onboarding/signup.html', form=form)

        account = Account(
           first_name = form.first_name.data,
           last_name = form.last_name.data,
           phone_number = form.phone_number.data,
           password = form.password.data,
           time_created = datetime.now(),
           time_updated = datetime.now())
        current_app.db_session.add(account)
        current_app.db_session.commit()

        # verify phone
        session['account_id'] = account.id
        verification_code = generate_and_store_new_verification_code(account)
        target_phone = '+1' + form.phone_number.data.replace('-','')
        services.phone.send_message(target_phone, constants.PHONE_VERIFICATION_MSG.format(verification_code))
        return redirect(url_for('onboarding_bp.verify_phone_number'))
    return render_template('onboarding/signup.html', form=form)


@onboarding_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        try:
            account = get_account_by_phone_number(form.phone_number.data)
            if account == None:
                flash(constants.INVALID_CREDENTIALS)
                return render_template('onboarding/login.html', form=form)

            # print 'Account = ',account,' Status = ',account.status
            if account.status == Account.UNVERIFIED:
                session['account_id'] = account.id
                flash(constants.ACCOUNT_NOT_VERIFIED)
                return redirect(url_for('onboarding_bp.verify_phone_number'))
            elif account.password_match(form.password.data) and account.status == Account.VERIFIED_PHONE:
                # session['logged_in'] = True
                # session['account_id'] = account.id
                login_user(account)
                next = request.args.get('next')
                # next_is_valid should check if the user has valid
                # permission to access the `next` url
                # print 'Next page =',next,' is_valid_next =',next_is_valid(next)
                # if not next_is_valid(next):
                #     return flask.abort(404)
                return redirect(next or url_for('onboarding_bp.dashboard'))
        except Exception as e:
            print 'Exception::',e
            print traceback.format_exc()
            return render_template('404.html')
    return render_template('onboarding/login.html', form=form)

def fetch_financial_information():
    for fi in current_user.fis:
        response = get_bank_info(fi.bank_account_id)
        fi.available_balance = response['available_balance']
        fi.current_balance = response['current_balance']
        fi.subtype = response['subtype']
        fi.subtype_name = response['subtype_name']
        fi.account_number_last_4 = response['account_number_last_4']
        fi.institution_type = response['institution_type']

@onboarding_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('.login'))

@onboarding_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    if current_user.status != Account.VERIFIED_PHONE:
        flash({
            'content':'Please verify your phone first',
            'class': 'error'
        })
        return redirect(url_for('.verify_phone_number'))
    valid_tabs = ['account', 'membership', 'transaction', 'bank']
    tab = request.args.get('tab')
    if tab not in valid_tabs:
        tab = 'account'
        
    data = {}
    # eligible_for_membership_reapplication = True
    # for membership in current_user.memberships:
    #     if membership.is_active() or membership.is_pending():
    #         eligible_for_membership_reapplication = False
    # data['eligible_for_membership_reapplication'] = eligible_for_membership_reapplication

    if len(current_user.memberships) == 0:
        data['show_notification'] = True
        data['notification_class'] = 'error'
        data['notification_message_description'] = 'You application is incomplete'
        data['notification_message_title'] = 'Apply Now'
        data['notification_url'] = 'onboarding_bp.apply_for_membership'
    elif len(current_user.fis) == 0:
        data['show_notification'] = True
        data['notification_class'] = 'error'
        data['notification_message_description'] = 'You have not added bank account yet'
        data['notification_message_title'] = 'Add Bank'
        data['notification_url'] = 'onboarding_bp.add_bank'
    elif has_unverified_bank_account():
        data['show_notification'] = True
        data['notification_class'] = 'error'
        data['notification_message_description'] = 'You have not verified your bank account'
        data['notification_message_title'] = 'Verify Account'
        data['notification_url'] = 'onboarding_bp.verify_account_random_deposit'
    return render_template('onboarding/dashboard.html', data=data, tab=tab)

def has_unverified_bank_account():
    for fi in current_user.fis:
        if fi.status == Fi.UNVERFIED:
            return True
    return False

@onboarding_bp.route('/home', methods=['GET'])
@login_required
def account():
    if current_user.status != Account.VERIFIED_PHONE:
        flash({
            'content':'Please verify your phone first',
            'class': 'error'
        })
        return redirect(url_for('.verify_phone_number'))

    data = {}
    eligible_for_membership_reapplication = True
    for membership in current_user.memberships:
        if membership.is_active() or membership.is_pending():
            eligible_for_membership_reapplication = False
    data['eligible_for_membership_reapplication'] = eligible_for_membership_reapplication

    print '*****************user hasnt applied for membership = ', len(current_user.memberships)
    if len(current_user.memberships) == 0:
        data['show_notification'] = True
        data['notification_message'] = 'You application is incomplete'
        data['notification_url'] = 'onboarding_bp.apply_for_membership'

    return render_template('onboarding/account.html', data=data)

@onboarding_bp.route('/apply_for_membership', methods=['GET'])
@login_required
def apply_for_membership():
    if len(current_user.memberships) == 0:
        return redirect(url_for('.enter_personal_information'))

    memberships = sorted(current_user.memberships, key=lambda m: m.time_created, reverse = True)
    if memberships[0].status == Membership.PENDING:
        flash('You have already applied for membership.')
        return redirect(url_for('.account'))

    return redirect(url_for('.enter_personal_information'))

@onboarding_bp.route('/enter-personal-information', methods=['GET', 'POST'])
@login_required
def enter_personal_information():
    if has_entered_personal_information(current_user):
        return redirect(url_for('.enter_employer_information'))

    form = PersonalInformationForm(request.form)
    print 'errors =',form.dob.errors,' date = ',form.dob.data
    if form.validate_on_submit():
        address = Address(
        street1 = form.street1.data,
        street2 = form.street2.data,
        city = form.city.data,
        state = form.state.data,
        address_type = Address.INDIVIDUAL,
        postal_code = form.postal_code.data)
        address.account_id = current_user.id

        # current_app.db_session.add(address)
        current_user.email = form.email.data
        current_user.ssn = form.ssn.data.replace('-','')
        current_user.dob = form.dob.data
        current_user.time_updated = datetime.now()
        current_user.driver_license_number = form.driver_license_number.data
        current_user.addresses.append(address)

        current_app.db_session.add(current_user)
        current_app.db_session.commit()

        return redirect(url_for('.enter_employer_information'))

    breadcrumItems = get_breadcrum()
    breadcrumItems[0]['active'] = True
    return render_template('onboarding/enter_personal_information.html',
    form=form, breadcrumItems = breadcrumItems)

def get_breadcrum():
    breadcrumItems = [
        {
            'name': 'Enter personal information',
            'active': False
        },
        {
            'name': 'Enter employer information',
            'active': False
        },
        {
            'name': 'Select plan',
            'active': False
        },
        {
            'name': 'Add bank account',
            'active': False
        },
    ]
    return breadcrumItems

@onboarding_bp.route('/enter_employer_information', methods=['GET', 'POST'])
@login_required
def enter_employer_information():
    if has_entered_employer_information(current_user):
        return redirect(url_for('.select_plan'))

    form = EmployerInformationForm(request.form)
    print 'error = ',form.errors
    if form.validate_on_submit():
        try:
            print 'About to save employer information...'
            employer_address = Address(
            street1 = form.employer_street1.data,
            street2 = form.employer_street2.data,
            city = form.employer_city.data,
            state = form.employer_state.data,
            address_type = Address.EMPLOYER,
            postal_code = form.employer_postal_code.data)
            employer_address.account_id = current_user.id
            current_app.db_session.add(employer_address)

            current_user.employer_name = form.employer_name.data
            current_user.employer_phone_number = form.employer_phone_number.data
            current_user.time_updated = datetime.now()

            current_app.db_session.add(current_user)
            current_app.db_session.commit()
        except Exception as e:
            logging.info('failed to save employer information %s' % e)
            flash(constants.PLEASE_TRY_AGAIN)
            breadcrumItems = get_breadcrum()
            breadcrumItems[1]['active'] = True
            return render_template('onboarding/enter_employer_information.html',
            form=form, breadcrumItems = breadcrumItems)
        return redirect(url_for('.select_plan'))
    else:
        breadcrumItems = get_breadcrum()
        breadcrumItems[1]['active'] = True
        return render_template('onboarding/enter_employer_information.html',
        form=form, breadcrumItems = breadcrumItems)


@onboarding_bp.route('/select_plan', methods=['GET', 'POST'])
@login_required
def select_plan():
    form = SelectPlanForm(request.form)
    plans = get_all_plans()
    if form.validate_on_submit():
        plan_id = form.plan_id.data
        try:
            membership = Membership(
                account_id = current_user.id,
                status = Membership.PENDING,
                plan = get_plan_by_id(plan_id),
                time_updated = datetime.now(),
                time_created = datetime.now())
            current_user.memberships.append(membership)
            current_app.db_session.commit()
            return redirect(url_for('.add_bank'))
        except Exception as e:
            logging.error('Failed to save membership info %s for user %s, exception %s'
            % (membership, current_user, e))
            flash(constants.PLEASE_TRY_AGAIN)
    breadcrumItems = get_breadcrum()
    breadcrumItems[2]['active'] = True
    return render_template('onboarding/select_plan.html', form=form, plans=plans, breadcrumItems = breadcrumItems)

@onboarding_bp.route('/apply_next', methods=['POST', 'POST'])
def apply_next():
    return redirect(url_for('onboarding_bp.add_bank'))

# AJAX CALL
@onboarding_bp.route('/add_bank', methods=['GET', 'POST'])
@login_required
def add_bank():
    if request.method == 'GET':
        if len(current_user.memberships) == 0:
            return redirect(url_for('.apply_for_membership'))

        institutions = get_all_iav_supported_institutions()
        breadcrumItems = get_breadcrum()
        breadcrumItems[3]['active'] = True
        return render_template('onboarding/add_bank.html',
        institutions = institutions, breadcrumItems = breadcrumItems)
    else:
        try:
            public_token = request.form['public_token']
            account_id = request.form['account_id']
            account_name = request.form['account_name']
            institution = request.form['institution']
            institution_type = request.form['institution_type']

            response = json.loads(exchange_token(public_token, account_id))
            result = {}
            if get_fi_by_access_token(response['account_id']) is not None:
                result['error'] = True
                result['message'] = constants.BANK_ALREADY_ADDED
                return jsonify(result)

            fi = Fi(
                account_name = account_name,
                bank_account_id = account_id,
                institution = institution,
                institution_type = institution_type,
                verification_type = Fi.INSTANT,
                status = Fi.VERIFIED,
                access_token = response['access_token'],
                stripe_bank_account_token = response['stripe_bank_account_token'],
                time_updated = datetime.now(),
                time_created = datetime.now())
            current_user.fis.append(fi)

            logging.info('fetching financial information...')
            fetch_financial_information()
            logging.info('received financial information...')

            # Approving the membership for demo purpose. Will change in future.
            current_user.memberships.sort(key=lambda x: x.time_created)
            current_user.memberships[0].status = Membership.APPROVED

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

@onboarding_bp.route('/add_random_deposit', methods=['GET', 'POST'])
@login_required
def add_random_deposit():
    form = RandomDepositForm(request.form)
    if form.validate_on_submit():
        response = current_app.stripe_client.add_customer_bank(
            current_user.stripe_customer_id,
            account_number = form.account_number.data,
            routing_number = form.routing_number.data,
            currency = form.currency.data,
            country = form.country.data,
            account_holder_name = form.name.data)
        logging.info('Added bank account to stripe resposne = {}'.format(response))
        current_user.fis.append(Fi(
            institution = response['bank_name'],
            account_number_last_4 = response['last4'],
            bank_account_id = response['id'],
            verification_type = Fi.RANDOM_DEPOSIT,
            status = Fi.UNVERFIED,
            time_updated = datetime.now(),
            time_created = datetime.now(),
            access_token = common.generate_fake_token(5)))
        # current_user.fi.verification_type = Fi.RANDOM_DEPOSIT

        current_app.db_session.add(current_user)
        current_app.db_session.commit()
        return redirect(url_for('.application_complete'))
    else:
        return render_template('onboarding/random_deposit.html', form = form)

@onboarding_bp.route('/start_account_verify_random_deposit', methods=['POST'])
@login_required
def start_account_verify_random_deposit():
    fi_id = request.form['id']
    print 'called start_account_verify_random_deposit...'
    logging.info('Starting bank verification of fi id %s ' % fi_id)
    session[constants.FI_ID_KEY] = fi_id
    return redirect(url_for('.verify_account_random_deposit'))

@onboarding_bp.route('/verify_account_random_deposit', methods=['GET', 'POST'])
@login_required
def verify_account_random_deposit():
    logging.info('verify_account_random_deposit called with id = %s' % session[constants.FI_ID_KEY])
    form = RandomDepositVerifyAccountForm(request.form)
    if form.validate_on_submit():
        try:
            if session[constants.FI_ID_KEY] is None:
                raise Exception('Missing information for bank account verification')

            bank_account_id = None
            for fi in current_user.fis:
                if fi.id == int(session[constants.FI_ID_KEY]):
                    bank_account_id = fi.bank_account_id
                    break

            logging.info('About to verify bank account %s, customer id %s deposit1 %s deposit2 %s '
            % (bank_account_id, current_user.stripe_customer_id, form.deposit1.data, form.deposit2.data))

            response = current_app.stripe_client.verify_customer_bank(
                current_user.stripe_customer_id,
                bank_account_id,
                form.deposit1.data,
                form.deposit2.data)
            logging.info('Verified bank account, response = ',response)
            fi.status = Fi.VERIFIED
            fi.time_updated = datetime.now()

            current_app.db_session.add(fi)
            current_app.db_session.commit()

            flash({
                'class': 'info',
                'content':'Bank account has been verified'})
            return redirect(url_for('.account'))
        except Exception as e:
            logging.error('failed to verify_account_random_deposit, exception %s' % e)
            flash('Amounts does not match. Please try again')
            return render_template('onboarding/verify_account_random_deposit.html', form=form)
    else:
        return render_template('onboarding/verify_account_random_deposit.html', form=form)

@onboarding_bp.route('/application_complete', methods=['GET'])
@login_required
def application_complete():
    return render_template('onboarding/success.html')


def exchange_public_token(public_token, account_id):
    Client.config({
        'url': 'https://tartan.plaid.com'
    })
    client = Client(
    client_id=current_app.config['CLIENT_ID'],
    secret=current_app.config['CLIENT_SECRET'])

    #exchange token
    response = client.exchange_token(public_token)
    print 'token exhcnage response = %s' % client.access_token
    pprint(client)

    return {
        'access_token': client.access_token,
        'stripe_bank_account_token': client.stripe_bank_account_token
    }

def exchange_token(public_token, account_id):
    payload = {
        'client_id':current_app.config['CLIENT_ID'],
        'secret':current_app.config['CLIENT_SECRET'],
        'public_token':public_token,
        'account_id':account_id
    }
    print 'payload ',json.dumps(payload)

    response = requests.post('https://tartan.plaid.com/exchange_token', data=payload)

    # print 'response = ',response.text, 'code = ',response.status_code
    if response.status_code == requests.codes.ok:
        return response.text
    else:
        raise Exception('Failed to exchange token')

def get_bank_info(bank_account_id):
    if len(current_user.fis) == 0:
        return
    Client.config({'url': 'https://tartan.plaid.com'})
    client = Client(
    client_id=current_app.config['CLIENT_ID'],
    secret=current_app.config['CLIENT_SECRET'],
    access_token=current_user.fis[0].access_token)
    response = client.auth_get().json()
    print response

    ai = {}
    for account in response['accounts']:
        if account['_id'] == bank_account_id:
            ai['available_balance'] = account['balance']['available']
            ai['current_balance'] = account['balance']['current']
            ai['subtype'] = account['subtype']
            ai['subtype_name'] = account['meta']['name']
            ai['account_number_last_4'] = account['meta']['number']
            ai['institution_type'] = account['institution_type']
            return ai

def has_entered_personal_information(user):
    if user.ssn == None or user.dob == None or user.driver_license_number == None:
        return False

    for address in user.addresses:
        if address.type == Address.INDIVIDUAL:
            return True

    return False

def has_entered_employer_information(user):
    if user.employer_name == None or user.employer_phone_number == None:
        return False
    for address in user.addresses:
        if address.type == Address.BUSINESS:
            return True

    return False


# curl https://tartan.plaid.com/exchange_token \
#    -d client_id="57bbc58566710877408d093e" \
#    -d secret="0f3e8ecc989e5e6ed776b732d76161" \
#    -d public_token="304cb58348ae917b3afe2b430a45b87744ffd1884a9fae31ba87869fe1222983cd626d9c27a92ef92b64393fdccfadb41eec4abce649d0d974e70314964e04cf" \
#    -d account_id="nban4wnPKEtnmEpaKzbYFYQvA7D7pnCaeDBMy"
