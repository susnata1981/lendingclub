from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify
from flask import current_app, session
from plaid import Client
from forms import SignupForm, LoginForm, PhoneVerificationForm, PersonalInformationForm
from model import *
from .. import services
from .. import util
import random
import traceback
from datetime import datetime
from flask.ext.login import current_user, login_required, login_user, logout_user
from pprint import pprint
import requests
import json

onboarding_bp = Blueprint('onboarding_bp', __name__, url_prefix='/account')

def generate_and_store_new_verification_code(account):
    verification_code = random.randint(1000, 9999)
    account.phone_verification_code = verification_code
    current_app.db_session.add(account)
    current_app.db_session.commit()
    return verification_code

@onboarding_bp.route('/start', methods=['GET'])
def start():
    session['name'] = 'Joe'
    return render_template('onboarding/verifybank.html')

@onboarding_bp.route('/verify', methods=['GET', 'POST'])
def verify_phone_number():
    form = PhoneVerificationForm(request.form)
    if form.validate_on_submit():
        account = get_account_by_id(session['account_id'])
        # print 'Account = ',account,' Status = ',account.status,' verification code = ',account.phone_verification_code, 'form vc =',form.verification_code.data, ' vc type = ', type(account.phone_verification_code)
        if account.status == int(Account.UNVERIFIED) and \
        form.verification_code.data == account.phone_verification_code:
            account.status = Account.VERIFIED_PHONE
            current_app.db_session.add(account)
            current_app.db_session.commit()
            return redirect(url_for('onboarding_bp.login'))
        else:
            flash('Invalid verification code')
    return render_template('onboarding/verify.html', form=form)

# ajax
@onboarding_bp.route('/resend_verification', methods=['POST'])
def resend_verification():
    print 'account id =',session['account_id']
    if session['account_id'] is None:
        return jsonify({
            'error': True,
            'description': util.constants.MISSING_ACCOUNT
        })
    try:
        account = get_account_by_id(session['account_id'])
        verification_code = generate_and_store_new_verification_code(account)
        target_phone = '+1' + account.phone_number
        services.phone.send_message(target_phone, util.constants.PHONE_VERIFICATION_MSG.format(verification_code))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({
            'error': True,
            'description': traceback.print_exc()
        })

@onboarding_bp.route('/', methods=['GET', 'POST'])
def signup():
    print 'current user =',current_user
    if current_user.is_authenticated:
        print 'redirecting to account'
        return redirect(url_for('.account'))

    form = SignupForm(request.form)
    if form.validate_on_submit():
        account = Account(
           first_name = form.first_name.data,
           last_name = form.last_name.data,
           phone_number = form.phone_number.data,
           password = form.password.data)
        current_app.db_session.add(account)
        current_app.db_session.commit()

        # verify phone
        session['account_id'] = account.id
        verification_code = generate_and_store_new_verification_code(account)
        target_phone = '+1' + form.phone_number.data.replace('-','')
        services.phone.send_message(target_phone, util.constants.PHONE_VERIFICATION_MSG.format(verification_code))
        return redirect(url_for('onboarding_bp.verify_phone_number'))
    return render_template('onboarding/signup.html', form=form)


@onboarding_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    print 'request type = ',request.method
    if form.validate_on_submit():
        try:
            account = get_account_by_phone_number(form.phone_number.data)
            if account == None:
                flash(util.constants.INVALID_CREDENTIALS)
                return render_template('onboarding/login.html', form=form)

            # print 'Account = ',account,' Status = ',account.status
            if account.status == Account.UNVERIFIED:
                session['account_id'] = account.id
                flash(util.constants.ACCOUNT_NOT_VERIFIED)
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
                return redirect(next or url_for('onboarding_bp.account'))
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
    # current_app.db_session.commit()

@onboarding_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('.login'))

@onboarding_bp.route('/home', methods=['GET'])
@login_required
def account():
    data = {}
    rejected_for_membership_before = True
    for membership in current_user.memberships:
        # membership['status'] = membership.get_status()
        if membership.is_active():
            rejected_for_membership_before = False

    rejected_for_membership_before = False if len(current_user.memberships) == 0 \
    else rejected_for_membership_before

    data['eligible_for_membership_reapplication'] = rejected_for_membership_before
    return render_template('onboarding/account.html', data=data)

@onboarding_bp.route('/apply-enter-personal-information', methods=['GET', 'POST'])
@login_required
def apply_enter_personal_information():
    if has_applied_before(current_user):
        return redirect(url_for('.add_bank'))

    form = PersonalInformationForm(request.form)
    if form.validate_on_submit():
        address = Address(
        street1 = form.street1.data,
        street2 = form.street2.data,
        city = form.city.data,
        state = form.state.data,
        postal_code = form.postal_code.data)
        address.account_id = current_user.id

        current_app.db_session.add(address)
        current_user.email = form.email.data
        current_user.ssn = form.ssn.data.replace('-','')
        current_app.db_session.add(current_user)

        current_app.db_session.commit()
        return redirect(url_for('.add_bank'))
    return render_template('onboarding/enter_personal_information.html', form=form)


@onboarding_bp.route('/apply_next', methods=['POST', 'POST'])
def apply_next():
    return redirect(url_for('onboarding_bp.add_bank'))

@onboarding_bp.route('/add_bank', methods=['GET', 'POST'])
@login_required
def add_bank():
    if request.method == 'GET':
        return render_template('onboarding/add_bank.html')
    else:
        try:
            public_token = request.form['public_token']
            account_id = request.form['account_id']
            account_name = request.form['account_name']
            institution = request.form['institution']
            institution_type = request.form['institution_type']

            print('ADD BANK REQUEST account_id = {0}, account_name = {1}, institution = {2}, institution_type = {3}')\
            .format(account_id, account_name, institution, institution_type)
            # metadata = request.form['metadata']
            # print "METADATA = ",jsonify(metadata)

            response = json.loads(exchange_token(public_token, account_id))

            fi = Fi(
                account_name = account_name,
                bank_account_id = account_id,
                institution = institution,
                institution_type = institution_type,
                account_type = '',
                access_token = response['access_token'],
                stripe_bank_account_token = response['stripe_bank_account_token'],
                time_updated = datetime.now(),
                time_created = datetime.now())
            current_user.fis.append(fi)

            current_user.memberships.append(Membership(
                account_id = current_user.id,
                status = Membership.PENDING,
                time_updated = datetime.now(),
                time_created = datetime.now()))

            fetch_financial_information()

            current_app.db_session.add(current_user)
            current_app.db_session.commit()

            response = {}
            response['success'] = 'true'
            return redirect(url_for('.account'))
            # return jsnoify(response)
        except Exception as e:
            print e
            response = {}
            response['error'] = 'true'
            # response['description'] = e
            return jsonify(response)

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

    print 'response = ',response.text, 'code = ',response.status_code
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

def has_applied_before(user):
    return user.ssn != None and user.email != None and user.address != None


# curl https://tartan.plaid.com/exchange_token \
#    -d client_id="57bbc58566710877408d093e" \
#    -d secret="0f3e8ecc989e5e6ed776b732d76161" \
#    -d public_token="304cb58348ae917b3afe2b430a45b87744ffd1884a9fae31ba87869fe1222983cd626d9c27a92ef92b64393fdccfadb41eec4abce649d0d974e70314964e04cf" \
#    -d account_id="nban4wnPKEtnmEpaKzbYFYQvA7D7pnCaeDBMy"
