from flask import current_app
from datetime import datetime, timedelta
from shared.db.model import *
from shared.util import util, logger, error, constants

MIN_APR = .36
MAX_APR = .99
LOAN_AMOUNT_KEY = 'loan_amount'
LOAN_DURATION_KEY = 'loan_duration'
LOAN_REQUEST_KEY = 'loan_request'
LOGGER = logger.getLogger('shared.bli.account')

def get_total_interest(amount, duration, apr):
    return (amount * apr * duration) / 12

def get_monthly_payment(amount, duration, apr):
    return (amount + get_total_interest(amount, duration, apr)) / duration

def get_payment_plan_estimate(loan_amount, loan_duration):
    result = {}
    result['summary'] = {}
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
    LOGGER.info('create_request entry')
    if get_all_open_loans(account):
        LOGGER.error('User:%s has open loans. Cannot create a new loan' % (account.id))
        raise error.AccountHasOpenLoanError('User:%s has open loans. Cannot create a new loan' % (account.id))

    now = datetime.now()
    req_money.time_created = now
    req_money.time_updated = now
    try:
        account.request_money_list.append(req_money)
        current_app.db_session.add(account)
        current_app.db_session.commit()
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)
    LOGGER.info('create_request exit')

def get_all_open_loans(account):
    LOGGER.info('get_all_open_loans entry')
    try:
        open_loans = current_app.db_session.query(RequestMoney).filter(
        RequestMoney.account_id == account.id, RequestMoney.status.in_([RequestMoney.IN_REVIEW, RequestMoney.APPROVED, RequestMoney.ACCEPTED, RequestMoney.TRANSFER_IN_PROGRESS, RequestMoney.ACTIVE, RequestMoney.DELINQUENT, RequestMoney.IN_COLLECTION])
        ).all()
        return open_loans
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)
    LOGGER.info('get_all_open_loans exit')

def get_loan_summary(loan):
    LOGGER.info('get_loan_summary entry')
    summary = {}
    summary['loan_id'] = loan.id
    summary['status'] = loan.status
    summary['amount'] = loan.amount
    summary['date_applied'] = loan.time_created
    summary['duration'] = loan.duration
    summary['bank_last_4'] = loan.fi.account_number_last_4
    summary['bank_name'] = loan.fi.institution
    if loan.apr:
        summary['apr'] = loan.apr
    else:
        summary['apr'] = 'N/A'
    if not loan.status in [RequestMoney.IN_REVIEW, RequestMoney.DECLINED] and loan.apr:
        summary['monthly_payment'] = get_monthly_payment(loan.amount, loan.duration, loan.apr)
        summary['total_interest'] = get_total_interest(loan.amount, loan.duration, loan.apr)
    else:
        summary['total_interest'] = 'N/A'
        summary['monthly_payment'] = 'N/A'
    LOGGER.info('get_loan_summary exit')
    return summary

def get_loan_schedule(loan):
    LOGGER.info('get_loan_schedule entry')
    schedule = []
    for tran in loan.transactions:
        schedule.append({
            'amount' : tran.amount,
            'date' : tran.due_date,
            'status' : tran.status
        })
    LOGGER.info('get_loan_schedule exit')
    return schedule

def get_loan_schedule_by_id(loan_id, account_id):
    LOGGER.info('get_loan_schedule_by_id entry')
    try:
        loan = current_app.db_session.query(RequestMoney).filter(
        RequestMoney.id == loan_id, RequestMoney.account_id == account_id).one_or_none()
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)
    if not loan:
        LOGGER.error('Loan(id=%s) not found for Account(id=%s)' % (loan_id, account_id))
        raise error.LoanNotFoundError('Loan(id=%s) not found for Account(id=%s)' % (loan_id, account_id))
    LOGGER.info('get_loan_schedule_by_id exit')
    return get_loan_schedule(loan)

def get_loan_activity(account):
    LOGGER.info('get_loan_activity entry')
    activity = []
    for loan in account.request_money_list:
        info = {}
        #loan summary
        info['summary'] = get_loan_summary(loan)
        #payment schedule
        info['repayment_schedule'] = get_loan_schedule(loan)
        #add to activity list
        activity.append(info)
    LOGGER.info('get_loan_activity exit')
    return activity
