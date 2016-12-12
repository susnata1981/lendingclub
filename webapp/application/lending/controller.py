from flask import Blueprint, render_template, session, request, redirect, url_for, jsonify
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
from shared.util import error, util
import traceback

DEBUG = True
lending_bp = Blueprint('lending_bp', __name__, url_prefix='/lending')
PREVIOUS_STATE = 'prev_state'

@lending_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    data = {}
    data['application_incomplete'] = not accountBLI.is_signup_complete(current_user)
    if not current_user.get_open_loans():
        #no loans, show apply loans
        data['can_apply_for_loan'] = True
    data['loans'] = lendingBLI.get_loan_activity(current_user)
    # data['loans'] = lendingBLI.fake_loan_summary()
    #pprint(data)
    return render_template('lending/dashboard.html', data=data)

@lending_bp.route('/loan_schedule', methods=['POST'])
@login_required
def loan_schedule():
    # print 'loan_id:', request.form.get('loan_id')
    loan_id = int(request.form.get('loan_id'))
    data = {}
    data['show_back_button'] = True
    try:
        data['schedule'] = lendingBLI.get_loan_schedule_by_id(loan_id, current_user.id)
        data['summary'] = lendingBLI.get_loan_summary_by_id(loan_id, current_user.id)
        pprint(data['summary'])
    except Exception as e:
        traceback.print_exc()
        logging.error('loan_schedule failed with exception: %s' % (e.message))
        util.flash_error(constants.GENERIC_ERROR)
    # pprint(data)
    return render_template('lending/_payment_schedule.html', data=data)

@lending_bp.route('/get_payment_plan_estimate', methods=['POST'])
def get_payment_plan_estimate():
    loan_amount = float(request.form.get('loan_amount'))
    loan_duration = int(request.form.get('loan_duration'))

    save_loan_request_to_session(loan_amount, loan_duration)
    result = lendingBLI.get_payment_plan_estimate(loan_amount, loan_duration)
    return render_template('lending/_loan_info.html', data=result)

@lending_bp.route('/loan_application', methods=['GET','POST'])
@login_required
def loan_application():
    open_loans = current_user.get_open_loans()
    if open_loans:
        logging.info('User:%d has open loans:%d.' % (current_user.id, len(open_loans)))
        util.flash_error('You already have %d open loan(s). You cannot take out more than 1 loan' % (len(open_loans)))
        return redirect(url_for('.dashboard'))
    if not accountBLI.is_signup_complete(current_user):
        logging.info('User:%d application is not complete.' % (current_user.id))
        util.flash_error('Please complete your signup before requesting a loan.')
        return redirect(url_for('.dashboard'))

    form = LoanApplicationForm()
    data = {}
    data['fis'] = current_user.get_usable_fis(Fi.VERIFIED)
    if request.method == 'GET':
        return render_template('lending/loan_application.html', data=data, form=form)
    else:
        #Question: can the java script be modified in the browser to send an amount greater than 1000 or less than 500?
        loan_amount = float(request.form.get('loan_amount'))
        loan_duration = int(request.form.get('loan_duration'))
        selected_fi_id = int(request.form.get('selected_fi_id'))
        # print 'loan_amount:%f, loan_duration:%d, fi_id:%d' % (loan_amount, loan_duration, selected_fi_id)
        #TODO: Compare form fieds with session fields
        req_money = RequestMoney(
            account_id = current_user.id,
            amount = loan_amount,
            duration = loan_duration,
            status = RequestMoney.IN_REVIEW,
            fi_id = selected_fi_id,
            time_updated = datetime.now(),
            time_created = datetime.now())
        try:
            req_money = lendingBLI.create_request(current_user, req_money)
            ### FOR DEMO ONLY #####
            req_money.status = RequestMoney.APPROVED
            req_money.apr = 0.55
            current_app.db_session.add(req_money)
            current_app.db_session.commit()
            ### END DEMO ONLY #####
            return render_template('lending/loan_application_completed.html')
        except Exception as e:
            if DEBUG:
                traceback.print_exc()
            logging.error('loan_application failed with exception %s' % e)
            data['error'] = True
            util.flash_error(constants.GENERIC_ERROR)
            return render_template('lending/loan_application.html', data=data, form=form)

@lending_bp.route('/loan_details', methods=['POST'])
@login_required
def loan_details():
    loan_id = int(request.form.get('loan_id'))
    data = {}
    try:
        logging.info('loan_details start')
        data = lendingBLI.get_approved_loan_payment_plan(loan_id, current_user.id)
        pprint(data)
    except Exception as e:
        # traceback.print_exc()
        logging.error('loan_details failed with exception: %s' % (e.message))
        util.flash_error(constants.GENERIC_ERROR)
    return render_template('lending/loan_details.html', data=data)

@lending_bp.route('/loan_details_confirm', methods=['POST'])
@login_required
def loan_details_confirm():
    loan_id = int(request.form.get('loan_id'))
    try:
        lendingBLI.process_loan_acceptance(loan_id, current_user.id)
        ### FOR DEMO ONLY #####
        loan = current_app.db_session.query(RequestMoney).filter(RequestMoney.id == loan_id, RequestMoney.account_id == current_user.id).one_or_none()
        loan.status = RequestMoney.ACTIVE
        current_app.db_session.add(loan)
        current_app.db_session.commit()
        ### END DEMO ONLY #####
        return render_template('lending/loan_accepted_success.html')
    except Exception as e:
        traceback.print_exc()
        logging.error('loan_schedule failed with exception: %s' % (e.message))
        util.flash_error(constants.GENERIC_ERROR)
        return redirect(url_for('.dashboard'))

@lending_bp.route('/start_payoff', methods=['GET'])
@login_required
def start_payoff():
    try:
        payoff = lendingBLI.get_payoff_information(current_user)
        session['payoff_loan_id'] = payoff.loan_id
        pprint(payoff.to_map())
        return render_template('lending/loan_payoff_details.html', data=payoff.to_map())
        #return jsonify(payoff.to_map())
    except error.NoOpenLoanFoundError as e:
        logging.error('start_payoff failed with NoOpenLoanFoundError: %s' % (e.message))
        util.flash_error('You don\'t have any loans that are eligible for payoff.')
        return redirect(url_for('.dashboard'))
    except error.HasInProgressTransactionError as e:
        logging.error('start_payoff failed with HasInProgressTransactionError: %s' % (e.message))
        util.flash_error('Currently you have one or more payments in progress on the open loan. Please try again after all the transactions have been processed.')
        return redirect(url_for('.dashboard'))
    except Exception as e:
        traceback.print_exc()
        logging.error('start_payoff failed with exception: %s' % (e.message))
        util.flash_error(constants.GENERIC_ERROR)
        return redirect(url_for('.dashboard'))

@lending_bp.route('/payoff', methods=['POST'])
@login_required
def payoff():
    if not 'payoff_loan_id' in session or not session['payoff_loan_id']:
        data['unauthorized'] = True
    loan_id = session['payoff_loan_id']
    session.pop('payoff_loan_id', None)
    try:
        #TODO: not getting the form data of the amounts th euser saw might result
        # in slightly more interest on day change between view and submit
        # Pass the payoof calculation instead
        lendingBLI.payoff(loan_id, current_user)
        return render_template('lending/loan_payoff_success.html')
    except Exception as e:
        traceback.print_exc()
        logging.error('payoff failed with exception: %s' % (e.message))
        #TODO: handle notification
        return redirect(url_for('.dashboard'))

##### helper functions ############
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

##### OLD
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
        util.flash_error('Currently you do not owe any money.')
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
        util.flash_error('Currently you do not owe any money.')
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
