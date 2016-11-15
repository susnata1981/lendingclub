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
from pprint import pprint
import requests
import json
import logging
import dateutil
from dateutil.relativedelta import relativedelta
from shared.bli import account as accountBLI
from shared.util import error

lending_bp = Blueprint('lending_bp', __name__, url_prefix='/lending')
PREVIOUS_STATE = 'prev_state'

@lending_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    data = {}
    data['application_incomplete'] = not accountBLI.is_application_complete(current_user)
    #TODO : add account data activity
    return render_template('account/dashboard.html', data=data)

@lending_bp.route('/complete_application', methods=['GET','POST'])
@login_required
def complete_application():
    next = accountBLI.application_next_step(current_user)
    if next['enter_employer_information']:
        return redirect(url_for('.enter_employer_information'))
    elif next['add_bank']:
        print 'TODO: add_bank'
        #return redirect(url_for('.add_bank'))
    elif next['verify_bank']:
        print 'TODO: verify_bank'
        #return redirect(url_for('.verify_bank', id=next['id']))
    return redirect(url_for('.dashboard'))

@lending_bp.route('/enter_employer_information', methods=['GET', 'POST'])
@login_required
def enter_employer_information():
    form = EmployerInformationForm(request.form)
    if form.validate_on_submit():
        try:
            now = datetime.now()
            employer = Employer(
                type = Employer.TYPE_FROM_NAME[form.employment_type.data],
                name = form.employer_name.data,
                phone_number = form.employer_phone_number.data,
                street1 = form.street1.data,
                street2 = form.street2.data,
                city = form.city.data,
                state = form.state.data,
                postal_code = form.postal_code.data,
                status = Employer.ACTIVE,
                time_created = now,
                time_updated = now
            )
            accountBLI.add_employer(current_user, employer)
            return redirect(url_for('.dashboard'))
        except error.DatabaseError as de:
            print 'ERROR: Database Exception: %s' % (de.message)
            flash(constants.GENERIC_ERROR)
            return render_template('account/enter_employer_information.html', form=form)
        except Exception as e:
            print 'ERROR: General Exception: %s' % (e.message)
            flash(constants.GENERIC_ERROR)
            return render_template('account/enter_employer_information.html', form=form)
    return render_template('account/enter_employer_information.html', form=form)

@lending_bp.route('/memberships', methods=['GET'])
@login_required
def get_membership_info():
    data = create_notifications()
    for t in current_user.request_money_list:
        if t.status != RequestMoney.PAYMENT_COMPLETED:
            if request.method == 'GET':
                data['show_notification'] = True
                data['notification_class'] = 'info'
                data['notification_message_description'] = 'You currently owe ${0} before {1}'.format(t.amount, t.payment_date.strftime("%d/%m/%Y"))
                request_money_enabled = False

    return render_template('onboarding/account-membership-section.html', data=data)

@lending_bp.route('/make_payment', methods=['GET', 'POST'])
@login_required
def make_payment():
    owes_money = False
    data = {}
    for request_money in current_user.request_money_list:
        if request_money.status == RequestMoney.PAYMENT_DUE:
            owes_money = True
            data['request_money'] = request_money

    if not owes_money:
        flash('Currently you do not owe any money.')
        return render_template('lending/make_payment.html', data=data)

    form = MakePaymentForm(request.form)
    if form.validate_on_submit():
        # do something
        session['payment_amount'] = form.payment_amount.data
        session['payment_date'] = datetime.now()
        session[PREVIOUS_STATE] = 'make_payment'
        return redirect(url_for('.confirm_payment'))

    return render_template('lending/make_payment.html', form=form, data=data);

@lending_bp.route('/confirm_payment', methods=['GET', 'POST'])
@login_required
def confirm_payment():
    print 'confirm_payment previous payment_amount = '
    if session[PREVIOUS_STATE] != 'make_payment':
        flash('Currently you do not owe any money.')
        return redirect(url_for('.dashboard'))

    data = {}
    data['payment_amount'] = session['payment_amount']
    if request.method.upper() == 'POST':
        session[PREVIOUS_STATE] = 'confirm_payment'
        return redirect(url_for('.payment_success'))
    elif request.method == 'GET':
        return render_template('lending/confirm_payment.html', data=data)

@lending_bp.route('/payment_success', methods=['GET', 'POST'])
@login_required
def payment_success():
    print 'payment_success previous payment_amount = '
    if session[PREVIOUS_STATE] != 'confirm_payment':
        return redirect(url_for('.dashboard'))

    data = {}
    data['payment_amount'] = session['payment_amount']
    data['payment_date'] = session['payment_date']
    return render_template('lending/payment_success.html', data=data)

@lending_bp.route('/request_money', methods=['GET','POST'])
@login_required
def request_money():
    form = RequestMoneyForm(request.form)
    data = create_notifications()
    request_money_enabled = False
    if current_user.memberships:
        current_user.memberships.sort(lambda x: x.time_created)
        request_money_enabled = current_user.memberships[0].status == Membership.APPROVED

    for t in current_user.request_money_list:
        if t.status != RequestMoney.PAYMENT_COMPLETED:
            data['show_notification'] = True
            data['notification_class'] = 'info' if request.method == 'GET' else 'error'
            data['notification_message_description'] = 'You currently owe ${0} before {1}'.format(t.amount, t.payment_date.strftime("%m/%d/%Y"))
            request_money_enabled = False
            return render_template('onboarding/request_money.html', data=data,
            request_money_enabled = request_money_enabled, form=form)

    if form.validate_on_submit():
        if form.requested_amount.data > current_user.memberships[0].plan.max_loan_amount:
            data = {}
            data['show_notification'] = True
            data['notification_class'] = 'error'
            data['notification_message_description'] = 'As per your membership plan, the maximum you can borrow is {}'.format(current_user.memberships[0].plan.max_loan_amount)
            return render_template('onboarding/request_money.html',
            data=data, request_money_enabled = request_money_enabled, form=form)
        try:
            print 'saving transaction...'
            today = datetime.now()
            payment_date = today + relativedelta(month=1)
            request_money = RequestMoney(
                account_id = current_user.id,
                amount = form.requested_amount.data,
                status = RequestMoney.PENDING,
                payment_date = payment_date,
                time_updated = today,
                time_created = today)

            current_user.request_money_list.append(request_money)
            current_app.db_session.add(current_user)
            current_app.db_session.add(request_money)
            current_app.db_session.commit()

            data = {}
            data['show_notification'] = True
            data['notification_class'] = 'info'
            data['notification_message_description'] = 'We have received your request to borrow ${0}. This will be transferred to your account in 1 business day'.format(form.requested_amount.data)
        except Exception as e:
            # traceback.print_exc()
            flash('Failed to process your request. Please try again.')
            logging.error('request_money failed with exception %s' % e)
    return render_template('onboarding/request_money.html',
    data=data, request_money_enabled = request_money_enabled, form=form)

@lending_bp.route('/transactions', methods=['GET'])
@login_required
def get_transaction_info():
    data = create_notifications()
    for t in current_user.request_money_list:
        if t.status != RequestMoney.PAYMENT_COMPLETED:
            data['show_notification'] = True
            data['notification_class'] = 'info'
            data['notification_message_description'] = 'You currently owe ${0} before {1}'.format(t.amount, t.payment_date.strftime("%m/%d/%Y"))

    return render_template('onboarding/transactions.html', data=data)

def next_month(date):
    future_date = date.today()+ relativedelta(months=1)
    return future_date.strftime('%m/%d/%Y')


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
    print 'getting bank info...'
    Client.config({
        'url': 'https://tartan.plaid.com',
        'suppress_http_errors': True
    })
    client = Client(
    client_id=current_app.config['CLIENT_ID'],
    secret=current_app.config['CLIENT_SECRET'],
    access_token=current_user.fis[0].access_token)

    # print 'response = ',client.auth_get()
    print '***************************** get-bank-info ='
    pprint(client.auth_get())
    response = client.auth_get().json()
    print 'get_bank_info response = ',response

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

def create_notifications():
    data = {}
    if not current_user.memberships:
        data['show_notification'] = True
        data['notification_class'] = 'error'
        data['notification_message_description'] = 'You application is incomplete'
        data['notification_message_title'] = 'Apply Now'
        data['notification_url'] = 'membership_bp.apply_for_membership'
    elif len(current_user.fis) == 0:
        data['show_notification'] = True
        data['notification_class'] = 'error'
        data['notification_message_description'] = 'You have not added bank account yet'
        data['notification_message_title'] = 'Add Bank'
        data['notification_url'] = 'membership_bp.add_bank'
    elif has_unverified_bank_account():
        data['show_notification'] = True
        data['notification_class'] = 'error'
        data['notification_message_description'] = 'You have not verified your bank account'
        data['notification_message_title'] = 'Verify Account'
        data['notification_url'] = 'membership_bp.verify_account_random_deposit'
    elif is_eligible_to_borrow() > 0:
        data['show_notification'] = True
        data['notification_class'] = 'info'
        data['notification_message_description'] = 'You can borrow money {0} times before 20th Nov 2017 by sending us a text @ 408-306-4444'.format(is_eligible_to_borrow())
    return data

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

def create_fake_membership_payments():
    m = current_user.memberships[0]
    for i in range(1):
        mp = MembershipPayment(
            membership_id = m.id,
            status = MembershipPayment.COMPLETED,
            time_updated = datetime.now() - dateutil.relativedelta.relativedelta(month=i),
            time_created = datetime.now() - dateutil.relativedelta.relativedelta(month=i))
        m.transactions.append(mp)
        current_app.db_session.add(m)
        current_app.db_session.add(mp)

def has_unverified_bank_account():
    for fi in current_user.fis:
        if fi.status == Fi.UNVERFIED:
            session[constants.FI_ID_KEY] = fi.id
            return True
    return False

def is_eligible_to_borrow():
    current_user.memberships.sort(key = lambda x : x.time_created)
    allowed_borrow_frequency = current_user.memberships[0].plan.loan_frequency

    if not current_user.request_money_list:
        return allowed_borrow_frequency
    for txn in current_user.request_money_list:
        if txn.status != RequestMoney.PAYMENT_COMPLETED:
            return 0

    return allowed_borrow_frequency - len(filter(lambda x: x.transaction_type == RequestMoney.BORROW, current_user.transactions))
