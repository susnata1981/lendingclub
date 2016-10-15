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

    def update_transaction_status(stripe_ref, status):
        #Stripe response handler web hook will call this function to update teh status
        #This function will load the corresponding transaction (and any child transactions if any) for update.
        #If the status of a balance payment is marked as completed, this function will also update the corresponding RequestMoney record
        pass
