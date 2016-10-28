from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify
from plaid import Client
from application.services import stripe_client
from forms import *
from application.db.model import *
import traceback
import random
from datetime import datetime
from flask.ext.login import current_user, login_required, login_user, logout_user
from application.util import constants, error
from application import services, common
from pprint import pprint
import requests
import json
import logging
import dateutil
from dateutil.relativedelta import relativedelta

lending_bp = Blueprint('lending_bp', __name__, url_prefix='/lending')

@lending_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    if current_user.status != Account.VERIFIED_PHONE:
        flash({
            'content':'Please verify your phone first',
            'class': 'error'
        })
        return redirect(url_for('account_bp.verify_phone_number'))
    valid_tabs = ['account', 'request_money', 'membership', 'transaction', 'bank']
    tab = request.args.get('tab')
    if tab not in valid_tabs:
        return redirect(url_for('.request_money'))

    data = {}
    form = RequestMoneyForm(request.form)

    if len(current_user.memberships) == 0:
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

    session['data'] = data
    if tab == 'request_money':
        return redirect(url_for('.request_money'))
    return render_template('onboarding/dashboard.html', data=data, tab=tab, form=form)

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

@lending_bp.route('/request_money', methods=['GET','POST'])
@login_required
def request_money():
    form = RequestMoneyForm(request.form)
    data = create_notifications()
    request_money_enabled = False
    if current_user.memberships:
        current_user.memberships.sort(lambda x: x.time_created)
        request_money_enabled = current_user.memberships[0].status == Membership.APPROVED

    print 'checking past transactions...'
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
    if len(current_user.memberships) == 0:
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
