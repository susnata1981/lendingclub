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
from model import RequestMoney, RequestMoneyHistory, Transaction, TransactionHistory

#TODO: This is just a place holder, need to implement the funcions

class TransactionService(object):
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.LOGGER = logger.getLogger(__name__)

    def __add_transaction_history(self, trans):
        self.LOGGER.info('Adding transaction:{0} history'.format(trans.id))
        trans_hist = TransactionHistory(
            id = trans.id,
            status = trans.status,
            memo = trans.memo,
            time_created = trans.time_updated)
        trans.history.append(trans_hist)
        self.db_session.add(trans_hist)

    def update_transaction_status(self, stripe_ref, status):
        #Stripe response handler web hook will call this function to update teh status
        #This function will load the corresponding transaction (and any child transactions if any) for update.
        #If the status of a balance payment is marked as completed, this function will also update the corresponding RequestMoney record
        pass

    def charge_interest(self, req):
        #Check the status of the request and charge interest for increments of 30 days from the start.
        #1) If the loan has been less than 2 * allowed due period - validation error
        #2) Will calculate how many charges should be there based on current date, in multiples of due date from the initial due date (maybe look at history)
        #3) If 1 & 2 validation pass charge interest for the due days period
        pass

    def payoff(self, req):
        #Check if interest needs to be paid for this month and then payoff balance
        #1) If it is after first due date, then charge no interest
        #2) If it is after the second due date, check if the interest has been charged, of not charge interest + balance
        #3) If not 1 or 2 then charge just balance
        pass

