from flask import current_app
from datetime import datetime, timedelta
from shared.db.model import *
from shared.util import util, logger, error, constants
from shared.bli.viewmodel.transaction import TransactionView, TransactionDetailView

MIN_APR = .36
MAX_APR = .99
DAYS_IN_LOAN_MONTH = 30
LOAN_AMOUNT_KEY = 'loan_amount'
LOAN_DURATION_KEY = 'loan_duration'
LOAN_REQUEST_KEY = 'loan_request'
LOGGER = logger.getLogger('shared.bli.lending')

def get_interest(amount, duration, apr):
    LOGGER.info('get_interest - amount:%s, duration:%s, apr:%s' % (amount, duration, apr))
    return (amount * apr * duration) / 12.0

def get_balance_for_each_interval(amount, duration):
    if duration > 0:
        return (float(amount)/duration)
    else:
        return 0

def get_total_payment(amount, duration, apr):
    return amount + get_interest(amount, duration, apr)

def get_monthly_payment(amount, duration, apr):
    return get_balance_for_each_interval(amount, duration) + get_interest(amount, 1, apr)

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
            'date': start_time + timedelta(days=DAYS_IN_LOAN_MONTH*(t+1))
        })
    return result

def create_request(account, req_money):
    LOGGER.info('create_request entry')
    if account.get_open_loans():
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
    return req_money

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
        summary['total_interest'] = get_interest(loan.amount, loan.duration, loan.apr)
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

def generate_schedule_item(amount, interest, date):
    td1 = TransactionDetailView(
        type = TransactionDetail.PRINCIPAL,
        amount = amount
    )
    td2 = TransactionDetailView(
        type = TransactionDetail.INTEREST,
        amount = interest
    )
    trans = TransactionView(
        type = Transaction.INSTALLMENT,
        status = Transaction.PENDING,
        amount = amount + interest,
        date = date,
        details = [td1, td2]
    )
    return trans

def calculate_loan_schedule(loan):
    LOGGER.info('calculate_loan_schedule Enter')
    monthly_balance = get_balance_for_each_interval(loan.amount, loan.duration)
    monthly_interest = get_interest(loan.amount, 1, loan.apr)
    # monthly_payment = get_monthly_payment(loan.amount, loan.duration, loan.apr)
    schedule = []
    start_time = datetime.now()
    for t in range(loan.duration):
        trans = generate_schedule_item(amount=monthly_balance, \
            interest=monthly_interest, date=(start_time + timedelta(days=DAYS_IN_LOAN_MONTH*(t+1))))
        schedule.append(trans.to_map())
    LOGGER.info('calculate_loan_schedule Exit')
    return schedule

def create_loan_schedule_transactions(loan, date):
    LOGGER.info('create_loan_schedule_transactions Enter')
    monthly_balance = get_balance_for_each_interval(loan.amount, loan.duration)
    monthly_interest = get_interest(loan.amount, 1, loan.apr)
    now = datetime.now()
    for i in range(loan.duration):
        s = generate_schedule_item(amount=monthly_balance, \
            interest=monthly_interest, date=(date + timedelta(days=DAYS_IN_LOAN_MONTH*(i+1))))
        trans = Transaction(
            transaction_type = s.type,
            status = s.status,
            amount = s.amount,
            due_date = s.date,
            time_created = now,
            time_updated = now
        )
        for td in s.details:
            trans_detail = TransactionDetail(
                type = td.type,
                amount = td.amount,
                time_created = now,
                time_updated = now
            )
            trans.details.append(trans_detail)
        loan.transactions.append(trans)
    LOGGER.info('create_loan_schedule_transactions Exit')

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
    try:
        create_loan_schedule_transactions(loan, now)
        current_app.db_session.add(loan)
        current_app.db_session.commit()
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)

def get_late_payment_transaction(trans, apr, till_date):
    principal = 0.0
    interest = 0.0
    for trans_detail in trans.details:
        if trans_detail.type == TransactionDetail.PRINCIPAL:
            principal = trans_detail.amount
        elif trans_detail.type == TransactionDetail.INTEREST:
            interest = trans_detail.amount
    now = datetime.now()
    td_principal = TransactionDetail(
        transaction_id = trans.id,
        type = TransactionDetail.PRINCIPAL,
        amount = principal,
        time_created = now,
        time_updated = now
    )
    td_interest = TransactionDetail(
        transaction_id = trans.id,
        type = TransactionDetail.INTEREST,
        amount = interest,
        time_created = now,
        time_updated = now
    )
    td_late_fee = TransactionDetail(
        transaction_id = trans.id,
        type = TransactionDetail.LATE_FEE,
        amount = LATE_FEE,
        time_created = now,
        time_updated = now
    )
    duration = float((till_date - trans.due_date).days) / DAYS_IN_LOAN_MONTH
    td_late_interest = TransactionDetail(
        transaction_id = trans.id,
        type = TransactionDetail.LATE_INTEREST,
        amount = get_interest(principal+interest, duration, apr),
        time_created = now,
        time_updated = now
    )
    details = [td_principal,td_interest,td_late_fee,td_late_interest]
    late_payment = Transaction(
        transaction_type = Transaction.LATE_PAYMENT,
        parent_id = trans.id,
        request_id = trans.request_id,
        status = Transaction.PENDING,
        amoount = td_principal.amount + td_interest.amount + td_late_fee.amount + td_late_interest.amount,
        due_date = till_date,
        initiated_by = Transaction.MANUAL,
        details = details,
        time_created = now,
        time_updated = now
    )
    return late_payment

def get_payoff_information(account):
    loan = account.get_payoff_eligible_loan()
    if not loan:
        LOGGER.error('No payoff eligible loan found for user:%s' % (account.id))
        raise error.NoOpenLoanFoundError('No open loans found for user:%s' % (account.id))

    in_progress_trans = loan.get_in_progress_transaction()
    if in_progress_trans:
        LOGGER.error('loan:%s has an in progress transactions(%s total)' % (loan.id, len(in_progress_trans)))
        raise error.HasInProgressTransactionError('loan:%s has one or more progress transactions(count=%s)' % (loan.id, len(in_progress_trans)))

    pd_principal = TransactionDetailView(
        type=TransactionDetail.PRINCIPAL,
        amount=loan.amount)
    pd_interest = TransactionDetailView(
        type=TransactionDetail.INTEREST,
        amount=0.0)
    pd_late_fee = TransactionDetailView(
        type=TransactionDetail.LATE_FEE,
        amount=0.0)
    pd_late_interest = TransactionDetailView(
        type=TransactionDetail.LATE_INTEREST,
        amount=0.0)

    payoff_int_start_date = None
    trans_list = sorted(loan.transactions, key=lambda x: x.due_date)
    #ASSUMPTION: Transactions will be completed in the order of their due date
    now = datetime.now()
    for trans in trans_list:
        if trans.transaction_type == Transaction.INSTALLMENT:
            if trans.status == Transaction.COMPLETED or trans.status == Transaction.FAILED:
                payoff_int_start_date = trans.due_date
                #ASSUMPTION: partial child payments not allowed, it has to be full principal of the parent
                children = trans.get_completed_child_transactions()
                if trans.status == Transaction.COMPLETED or \
                    (trans.status == Transaction.FAILED and children):
                    for trans_detail in trans.details:
                        if trans_detail.type == TransactionDetail.PRINCIPAL:
                            pd_principal.amount = pd_principal.amount - trans_detail.amount
                        #TODO: add code for other detail type, to show addl info like total interest paid so far...
                elif trans.status == Transaction.FAILED:
                    #this means no completed children
                    late_payment = get_late_payment_transaction(trans, loan.apr, now)
                    for trans_detail in late_payment.details:
                        #They still owe the principal for that installment, not subtracting from the pd_principal.amount
                        if trans_detail.type == TransactionDetail.INTEREST:
                            pd_interest.amount = pd_interest.amount + trans_detail.amount
                        elif trans_detail.type == TransactionDetail.LATE_FEE:
                            pd_late_fee.amount = pd_late_fee.amount + trans_detail.amount
                        elif trans_detail.type == TransactionDetail.LATE_INTEREST:
                            pd_late_interest.amount = pd_late_interest.amount + trans_detail.amount
    if not payoff_int_start_date:
        #This is when the user doesn't have atleast one completed or failed transaction
        payoff_int_start_date = loan.time_created
    duration = float((now - payoff_int_start_date).days) / DAYS_IN_LOAN_MONTH
    pd_interest.amount = pd_interest.amount + get_interest(loan.amount, duration, loan.apr)
    payoff_details = [pd_principal, pd_interest]
    if pd_late_fee.amount > 0:
        payoff_details.append(pd_late_fee)
    if pd_late_interest.amount > 0:
        payoff_details.append(pd_late_interest)
    payoff = TransactionView(
        loan_id = loan.id,
        type = Transaction.PAYOFF,
        status = Transaction.PENDING,
        amount = pd_principal.amount + pd_interest.amount + pd_late_fee.amount + pd_late_interest.amount,
        date = now,
        details = payoff_details
    )
    return payoff

def payoff(loan_id, account):
    LOGGER.info('payoff loan_id = '+str(loan_id)+' account_id:'+str(account.id)+' : Enter')
    try:
        loan = current_app.db_session.query(RequestMoney).filter(
        RequestMoney.id == loan_id, RequestMoney.account_id == account.id).one_or_none()
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)
    if not loan:
        LOGGER.error('No payoff eligible loan found for user:%s' % (account.id))
        raise error.NoOpenLoanFoundError('No open loans found for user:%s' % (account.id))
    now = datetime.now()
    for tran in loan.transactions:
        if tran.status == Transaction.PENDING:
            tran.status = Transaction.CANCELED
            tran.time_updated = now
    payoff = get_payoff_information(account)
    trans = Transaction(
        transaction_type = payoff.type,
        status = Transaction.IN_PROGRESS,
        amount = payoff.amount,
        due_date = payoff.date,
        time_created = now,
        time_updated = now
    )
    for td in payoff.details:
        trans_detail = TransactionDetail(
            type = td.type,
            amount = td.amount,
            time_created = now,
            time_updated = now
        )
        trans.details.append(trans_detail)
    loan.transactions.append(trans)
    # TODO: handle if stripe succeeds but DB write fails
    try:
        current_app.stripe_client.create_customer_charge(loan.account.stripe_customer_id,
        loan.fi.stripe_bank_account_token, (int)(payoff.amount*100), 'usd', 'payoff')
        current_app.db_session.add(loan)
        current_app.db_session.commit()
    except error.StripeError as e:
        LOGGER.error(e.message)
        raise e
    except Exception as e:
        LOGGER.error(e.message)
        raise error.DatabaseError(constants.GENERIC_ERROR,e)

def create_late_payment(loan, transaction):
    pass
