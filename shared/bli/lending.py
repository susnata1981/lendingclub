from flask import current_app
from datetime import datetime, timedelta
from shared.db import model
from shared.util import error, constants
import logging

MIN_APR = .36
MAX_APR = .99
LOAN_AMOUNT_KEY = 'loan_amount'
LOAN_DURATION_KEY = 'loan_duration'
LOAN_REQUEST_KEY = 'loan_request'

def get_payment_plan_estimate(loan_amount, loan_duration):
    result = {}
    result['summary'] = {}
    result['payment_schedule'] = {}
    result['summary']['loan_amount'] = loan_amount
    result['summary']['loan_duration'] = loan_duration

    start_time = datetime.now()

    min_payment = loan_amount + (loan_amount * MIN_APR * loan_duration) / 12
    max_payment = loan_amount + (loan_amount * MAX_APR * loan_duration) / 12
    monthly_payment_min = min_payment/loan_duration
    monthly_payment_max = max_payment/loan_duration
    expected_monthly_payment = (monthly_payment_min + monthly_payment_max) / 2

    result['summary']['min_payment'] = min_payment
    result['summary']['max_payment'] = max_payment
    result['summary']['min_apr'] = MIN_APR * 100
    result['summary']['max_apr'] = MAX_APR * 100
    result['summary']['min_interest'] = min_payment - loan_amount
    result['summary']['max_interest'] = max_payment - loan_amount
    result['summary']['monthly_payment_min'] = monthly_payment_min
    result['summary']['monthly_payment_max'] = monthly_payment_max
    result['summary']['expected_monthly_payment'] = expected_monthly_payment
    result['summary']['expected_interest_charge'] = expected_monthly_payment * loan_duration - loan_amount

    result['repayment_schedule'] = []
    for t in range(loan_duration):
        result['repayment_schedule'].append({
            'expected_amount': expected_monthly_payment,
            'date': start_time + timedelta(days=30*(t+1))
        })
    return result

def create_request(account, req_money):
    now = datetime.now()
    req_money.time_created = now
    req_money.time_updated = now
    try:
        account.request_money_list.append(req_money)
        current_app.db_session.add(account)
        current_app.db_session.commit()
    except Exception as e:
        logging.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)
