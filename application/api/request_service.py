from datetime import datetime, timedelta
import traceback

try:
    from application.util import error, logger, constants
    from application.db import model
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'util'))
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'db'))
    import error, logger, constants, model
from model import RequestMoney, RequestMoneyHistory, ExtensionRequest, ExtensionRequestHistory

class RequestService(object):
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.LOGGER = logger.getLogger(__name__)

    def __validate_request(self, req, valid_status, new_status):
        if not req:
            msg = "Invalid request:{0}".format(req)
            self.LOGGER.error(msg)
            raise AssertionError(msg)
        if req.status != valid_status:
            msg = 'Only requests in status:{0} can be moved to status:{1}. request id:{2} current status is:{3}'.format(
                    valid_status, new_status, req.id, req.status)
            self.LOGGER.info(msg)
            raise ValidationError(constants.INVALID_STATUS_REQUEST_APPROVAL_MESSAGE)
        #check if account is active and enrolled for a plan
        if not req.account.is_active():
            msg = 'Account:{0} is not verified, account status is:{1})'.format(req.account.id, req.account.status)
            self.LOGGER.error(msg)
            raise error.ValidationError(msg)
        else:
            plan = req.account.get_active_plan()
            if not plan:
                msg = 'Account:{} has not enrollled in any plans'.format(req.account.id)
                self.LOGGER()
                raise error.ValidationError(msg)

    def __add_request_history(self, req):
        self.LOGGER.info('Adding request:{0} history'.format(req.id))
        req_hist = RequestMoneyHistory(
            id = req.id,
            amount = req.amount,
            status = req.status,
            payment_date = req.payment_date,
            memo = req.memo,
            time_created = req.time_updated)
        req.history.append(req_hist)
        self.db_session.add(req_hist)

    def create_request(self, account, amount):
        #check if valid account
        if not account:
            msg = 'Invalid account:{0}'.format(account)
            self.LOGGER.error(msg)
            raise AssertionError(msg)
        #check if amount is valid
        if not amount:
            msg = 'Invalid amount:{0} for request_money by account:{1}'.format(amount, account.id)
            self.LOGGER.error(msg)
            raise AssertionError(msg)
        amt = float(amount)
        #check if account is active and enrolled for a plan
        plan = account.get_active_plan()
        if account.is_active() and plan:
            #check if any open requests
            open_request = account.get_open_request()
            if open_request != None:
                msg = 'Account:{0} already has an open request:{1} with status:{2}'.format(
                    account.id, open_request.id, open_request.status)
                self.LOGGER.error(msg)
                raise error.ValidationError(constants.YOU_OWE_MESSAGE.format(open_request.amount,open_request.payment_date))
            else:
                # check if amount is allowed by plan
                if amt > plan.max_loan_amount:
                    self.LOGGER.error('Account:{0} requested amount:{1} greater than subscribed amount:{2}'.format(
                        account.id, amt, plan.max_loan_amount))
                    raise error.ValidationError(constants.MAX_BORROW_MESSAGE.format(plan.max_loan_amount))
                now = datetime.now()
                due_date = now + timedelta(days=constants.DAYS_FOR_DUE_DATE)
                self.LOGGER.info('Saving account:{0} request money for amount:${1}'.format(account.id, amt))
                try:
                    req = RequestMoney(
                        account_id = account.id,
                        amount = amt,
                        status = RequestMoney.PENDING,
                        payment_date = due_date,
                        memo = None,
                        time_updated = now,
                        time_created = now)
                    account.request_money_list.append(req)
                    self.db_session.add(account)
                    self.db_session.add(req)
                    self.db_session.flush()
                    self.__add_request_history(req)
                    self.db_session.commit()
                    return req
                except Exception as e:
                    traceback.print_exc
                    self.LOGGER.error('request money failed with exception ',e)
                    raise e
        else:
            if not account.is_active():
                self.LOGGER.error('Account:{} is not verified(status:{})'.format(account.id, account.status))
                raise error.ValidationError(constants.ACCOUNT_ACTIVE_FOR_REQUEST_MONEY_MESSAGE)
            else:
                self.LOGGER('Account:{} has not enrollled in any plans'.format(account.id))
                raise error.ValidationError(constants.ACTIVE_PLAN_REQUIRED_MESSAGE)

    def approve_request(self, req):
        #check if the request is in PENDING state
        self.__validate_request(req, RequestMoney.PENDING, RequestMoney.IN_PROGRESS)
        now = datetime.now()
        due_date = now + timedelta(days=constants.DAYS_FOR_DUE_DATE)
        try:
            req.status = RequestMoney.IN_PROGRESS
            req.time_updated = now
            req.payment_date = due_date
            self.db_session.add(req)
            self.__add_request_history(req)
            self.db_session.commit()
        except Exception as e:
            traceback.print_exc
            self.LOGGER.error('Approving request money (id:{0}) failed with exception'.format(req.id),e)
            raise e

    def transfered_money(self, req):
        #check if the request is in IN_PROGRESS state
        self.__validate_request(req, RequestMoney.IN_PROGRESS, RequestMoney.TRANSFERRED)
        now = datetime.now()
        due_date = now + timedelta(days=constants.DAYS_FOR_DUE_DATE)
        try:
            req.status = RequestMoney.TRANSFERRED
            req.time_updated = now
            req.payment_date = due_date
            self.db_session.add(req)
            self.__add_request_history(req)
            self.db_session.commit()
        except Exception as e:
            traceback.print_exc
            self.LOGGER.error('Approving request money (id:{0}) failed with exception'.format(req.id),e)
            raise e

    def set_payment_due(self, req):
        #check if the request is in TRANSFERRED state
        self.__validate_request(req, RequestMoney.TRANSFERRED, RequestMoney.PAYMENT_DUE)
        now = datetime.now()
        due_date = now + timedelta(days=constants.DAYS_FOR_DUE_DATE)
        try:
            req.status = RequestMoney.PAYMENT_DUE
            req.time_updated = now
            req.payment_date = due_date
            self.db_session.add(req)
            self.__add_request_history(req)
            self.db_session.commit()
        except Exception as e:
            traceback.print_exc
            self.LOGGER.error('Approving request money (id:{0}) failed with exception'.format(req.id),e)
            raise e
