from flask import current_app
from datetime import datetime, timedelta
from shared.db.model import *
from shared.util import util, logger, error, constants

MIN_APR = .36
MAX_APR = .99
LOAN_AMOUNT_KEY = 'loan_amount'
LOAN_DURATION_KEY = 'loan_duration'
LOAN_REQUEST_KEY = 'loan_request'
LOGGER = logger.getLogger('shared.bli.lending')

def get_total_interest(amount, duration, apr):
    return (amount * apr * duration) / 12

def get_total_payment(amount, duration, apr):
    return amount + get_total_interest(amount, duration, apr)

def get_monthly_payment(amount, duration, apr):
    return get_total_payment(amount, duration, apr) / duration

def get_payment_plan_estimate(loan_amount, loan_duration):
    result = {}
    result['summary'] = {}
    result['summary']['loan_amount'] = loan_amount
    result['summary']['loan_duration'] = loan_duration

    min_payment = get_total_payment(loan_amount, loan_duration, MIN_APR)
    max_payment = get_total_payment(loan_amount, loan_duration, MAX_APR)
    monthly_payment_min = get_monthly_payment(loan_amount, loan_duration, MIN_APR)
    monthly_payment_max = get_monthly_payment(loan_amount, loan_duration, MAX_APR)
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
    start_time = datetime.now()
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

def fake_loan_summary():
    data = [{'schedule': [{'amount': 166.56,
                          'date': datetime(2017, 4, 17, 17, 50, 30),
                          'status': 0L},
                         {'amount': 166.56,
                          'date': datetime(2017, 3, 17, 17, 50, 30),
                          'status': 0L},
                         {'amount': 166.56,
                          'date': datetime(2017, 2, 17, 17, 50, 30),
                          'status': 0L},
                         {'amount': 166.56,
                          'date': datetime(2017, 1, 17, 17, 50, 30),
                          'status': 0L},
                         {'amount': 166.56,
                          'date': datetime(2016, 12, 17, 17, 50, 30),
                          'status': 0L}],
                        'summary': {'amount': 650.0,
                            'apr': 0.99,
                            'bank_last_4': 5204L,
                            'bank_name': 'USAA',
                            'date_applied': datetime(2016, 11, 17, 17, 50, 30),
                            'duration': 5L,
                            'loan_id': 3L,
                            'monthly_payment': 183.625,
                            'status': 6L,
                            'total_interest': 268.125}},
                        {'schedule': [],
                        'summary': {'amount': 650.0,
                            'apr': 0.40,
                            'bank_last_4': 5204L,
                            'bank_name': 'USAA',
                            'date_applied': datetime(2016, 11, 17, 17, 39, 49),
                            'duration': 4L,
                            'loan_id': 2L,
                            'monthly_payment': 216.125,
                            'status': 1L,
                            'total_interest': 214.5}},
                        {'schedule': [],
                        'summary': {'amount': 600.0,
                            'apr': 'N/A',
                            'bank_last_4': 5204L,
                            'bank_name': 'USAA',
                            'date_applied': datetime(2016, 11, 17, 14, 39, 9),
                            'duration': 3L,
                            'loan_id': 1L,
                            'monthly_payment': 'N/A',
                            'status': 3L,
                            'total_interest': 'N/A'}}]
    #pprint(jsonify(data))
    return data

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

def get_loan_summary_by_id(loan_id, account_id):
    LOGGER.info('get_loan_schedule_by_id entry loan_id = '+str(loan_id)+' account_id:'+str(account_id))
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
    return get_loan_summary(loan)

def get_loan_schedule_by_id(loan_id, account_id):
    LOGGER.info('get_loan_schedule_by_id entry loan_id = '+str(loan_id)+' account_id:'+str(account_id))
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
        info['schedule'] = get_loan_schedule(loan)
        #add to activity list
        activity.append(info)
    LOGGER.info('get_loan_activity exit')
    return activity

def calculate_loan_schedule(loan):
    LOGGER.info('calculate_loan_schedule Enter')
    monthly_payment = get_monthly_payment(loan.amount, loan.duration, loan.apr)
    start_time = datetime.now()
    schedule = []
    for t in range(loan.duration):
        schedule.append({
            'amount': monthly_payment,
            'date': start_time + timedelta(days=30*(t+1)),
            'status': Transaction.PENDING
        })
    LOGGER.info('calculate_loan_schedule Exit')
    return schedule

def get_approved_loan_payment_plan(loan_id, account_id):
    LOGGER.info('get_payment_plan loan_id = '+str(loan_id)+' account_id:'+str(account_id)+' : Enter')
    try:
        loan = current_app.db_session.query(RequestMoney).filter(
        RequestMoney.id == loan_id, RequestMoney.account_id == account_id).one_or_none()
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)
    if not loan:
        LOGGER.error('Loan(id=%s) not found for Account(id=%s)' % (loan_id, account_id))
        raise error.LoanNotFoundError('Loan(id=%s) not found for Account(id=%s)' % (loan_id, account_id))
    if loan.status != RequestMoney.APPROVED:
        LOGGER.error('Loan(id=%s) not in approved status.' % (loan_id))
        raise error.LoanNotInApprovedStatus('Loan(id=%s) not in approved status.' % (loan_id))
    result = {}
    result['summary'] = get_loan_summary(loan)
    result['schedule'] = calculate_loan_schedule(loan)
    LOGGER.info('get_payment_plan loan_id = '+str(loan_id)+' account_id:'+str(account_id)+' : Exit')
    return result

def process_loan_acceptance(loan_id, account_id):
    LOGGER.info('get_payment_plan loan_id = '+str(loan_id)+' account_id:'+str(account_id)+' : Enter')
    try:
        loan = current_app.db_session.query(RequestMoney).filter(
        RequestMoney.id == loan_id, RequestMoney.account_id == account_id).one_or_none()
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)
    if not loan:
        LOGGER.error('Loan(id=%s) not found for Account(id=%s)' % (loan_id, account_id))
        raise error.LoanNotFoundError('Loan(id=%s) not found for Account(id=%s)' % (loan_id, account_id))
    if loan.status != RequestMoney.APPROVED:
        LOGGER.error('Loan(id=%s) not in approved status.' % (loan_id))
        raise error.LoanNotInApprovedStatus('Loan(id=%s) not in approved status.' % (loan_id))

    now = datetime.now()
    loan.status = RequestMoney.ACCEPTED
    loan.time_updated = now
    data = calculate_loan_schedule(loan)
    for schedule in data:
        print ''
        loan.transactions.append(Transaction(
            transaction_type = Transaction.FULL,
            status = Transaction.PENDING,
            amount = float(schedule['amount']),
            due_date = schedule['date'],
            time_created = now,
            time_updated = now
        ))
    try:
        current_app.db_session.add(loan)
        current_app.db_session.commit()
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)
