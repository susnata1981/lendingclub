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
from shared.bli import lending as lendingBLI
from shared.bli import bank as bankBLI
from shared.util import error
from application.bank import controller as bank_controller

lending_bp = Blueprint('lending_bp', __name__, url_prefix='/lending')
PREVIOUS_STATE = 'prev_state'

@lending_bp.route('/reset_password', methods=['GET','POST'])
def reset_password():
    form = ResetPasswordForm(request.form)
    data = {}
    if form.validate_on_submit():
        email = form.email.data
        try:
            account = get_account_by_email(email)
            if not account:
                flash('Account for this email(%s) doesn\'t exist at Ziplly.' % (email))
            else:
                try:
                    accountBLI.initiate_reset_password(account)
                    data['email_sent'] = True
                except error.MailServiceError:
                    flash(constants.RESET_PASSWORD_EMAIL_SEND_FAILURE_MESSAGE)
        except Exception:
            flash(constants.GENERIC_ERROR)
    return render_template('lending/reset_password.html', data=data, form=form)

@lending_bp.route('/<id>/reset_password', methods=['GET','POST'])
def reset_password_verify(id):
    token = request.args.get(constants.VERIFICATION_TOKEN_NAME)
    account = None
    try:
        account = accountBLI.verify_password_reset(int(id), token)
    except error.DatabaseError as de:
        logging.error('ERROR: Database Exception: %s' % (de.message))
        flash(constants.GENERIC_ERROR)
    except Exception as e:
        logging.error(e.message)
    if account:
        session['password_account_id'] = account.id
    return redirect(url_for('.reset_password_confirm'))

@lending_bp.route('/reset_password_confirm', methods=['GET','POST'])
def reset_password_confirm():
    logging.info('reset_password_confirm entry')
    form = ResetPasswordConfirmForm(request.form)
    data = {}
    if not 'password_account_id' in session or not session['password_account_id']:
        data['unauthorized'] = True
    elif form.validate_on_submit():
        account = get_account_by_id(session['password_account_id'])
        try:
            accountBLI.reset_password(account, form.password.data)
            session.pop('password_account_id', None)
            login_user(account)
            logging.info('reset_password_confirm - redirect exit')
            return redirect(url_for('.dashboard'))
        except error.DatabaseError as de:
            print 'ERROR: Database Exception: %s' % (de.message)
            flash(constants.GENERIC_ERROR)
    logging.info('reset_password_confirm exit')
    return render_template('lending/reset_password_confirm.html', data=data, form=form)

@lending_bp.route('/get_payment_plan_estimate', methods=['POST'])
def get_payment_plan_estimate():
    loan_amount = float(request.form.get('loan_amount'))
    loan_duration = int(request.form.get('loan_duration'))

    save_loan_request_to_session(loan_amount, loan_duration)
    result = lendingBLI.get_payment_plan_estimate(loan_amount, loan_duration)
    return render_template('lending/loan-info.html', data=result)

@lending_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    data = {}
    data['application_incomplete'] = not accountBLI.is_signup_complete(current_user)
    if not accountBLI.get_all_open_loans(current_user):
        #no loans, show apply loans
        data['can_apply_for_loan'] = True
    #TODO : add account data activity
    return render_template('account/dashboard.html', data=data)

@lending_bp.route('/complete_signup', methods=['GET','POST'])
@login_required
def complete_signup():
    next = accountBLI.signup_next_step(current_user)
    if 'enter_employer_information' in next:
        return redirect(url_for('.enter_employer_information'))
    elif 'add_bank' in next:
        return redirect(url_for('bank_bp.add_bank'))
    elif 'verify_bank' in next:
        session[bankBLI.RANDOM_DEPOSIT_FI_ID_KEY] = next[bankBLI.RANDOM_DEPOSIT_FI_ID_KEY]
        return redirect(url_for('bank_bp.verify_random_deposit'))
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
            return redirect(url_for('.complete_signup'))
        except error.DatabaseError as de:
            print 'ERROR: Database Exception: %s' % (de.message)
            flash(constants.GENERIC_ERROR)
            return render_template('account/enter_employer_information.html', form=form)
        except Exception as e:
            print 'ERROR: General Exception: %s' % (e.message)
            flash(constants.GENERIC_ERROR)
            return render_template('account/enter_employer_information.html', form=form)
    return render_template('account/enter_employer_information.html', form=form)

@lending_bp.route('/loan_application', methods=['GET','POST'])
@login_required
def loan_application():
    form = LoanApplicationForm()
    data = {}
    data['fis'] = current_user.fis
    if request.method == 'GET':
        return render_template('lending/loan_application.html', data=data)
    else:
        print 'Loan application confirm called'
        #Question: can the java script be modified in the browser to send an amount greater than 1000 or less than 500?
        loan_amount = float(request.form.get('loan_amount'))
        loan_duration = int(request.form.get('loan_duration'))
        selected_fi_id = int(request.form.get('selected_fi_id'))
        print 'loan_amount:%f, loan_duration:%d, fi_id:%d' % (loan_amount, loan_duration, selected_fi_id)
        #TODO: Compare form fieds with session fields
        req_money = RequestMoney(
            account_id = current_user.id,
            amount = loan_amount,
            duration = loan_duration,
            status = RequestMoney.PENDING,
            fi_id = selected_fi_id,
            time_updated = datetime.now(),
            time_created = datetime.now())
        try:
            req_money = lendingBLI.create_request(current_user, req_money)
            return redirect(url_for('.dashboard'))
        except Exception as e:
            logging.error('loan_application failed with exception %s' % e)
            data['error'] = True
            flash(constants.GENERIC_ERROR)
            return render_template('lending/loan_application.html', data=data)

def save_loan_request_to_session(loan_amount=None, loan_duration=None):
    if current_user and current_user.is_authenticated:
        if lendingBLI.LOAN_REQUEST_KEY in session and session[lendingBLI.LOAN_REQUEST_KEY]:
            loan_request = session[lendingBLI.LOAN_REQUEST_KEY]
        else:
            loan_request = {}
        if loan_amount:
            loan_request[lendingBLI.LOAN_AMOUNT_KEY] = loan_amount
        if loan_duration:
            loan_request[lendingBLI.LOAN_DURATION_KEY] = loan_duration
        if loan_request:
            session[lendingBLI.LOAN_REQUEST_KEY] = loan_request

############################

# @lending_bp.route('/memberships', methods=['GET'])
# @login_required
# def get_membership_info():
#     data = create_notifications()
#     for t in current_user.request_money_list:
#         if t.status != RequestMoney.PAYMENT_COMPLETED:
#             if request.method == 'GET':
#                 data['show_notification'] = True
#                 data['notification_class'] = 'info'
#                 data['notification_message_description'] = 'You currently owe ${0} before {1}'.format(t.amount, t.payment_date.strftime("%d/%m/%Y"))
#                 request_money_enabled = False
#
#     return render_template('onboarding/account-membership-section.html', data=data)

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
