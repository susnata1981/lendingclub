import stripe, time, inspect, distutils, sys
from datetime import datetime, timedelta, date
from flask import current_app
from flask.ext.login import current_user

try:
    from shared.util import error, logger, constants
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'util'))
    import error, logger, constants

def init():
    current_app.stripe_client = init_standalone(current_app.config)

def init_standalone(config):
    api_key = 'test key'
    production_mode = config['ENABLE_PRODUCTION_MODE']
    if type(production_mode) != type(True):
        production_mode = distutils.util.strtobool(production_mode)

    if production_mode:
        api_key = config['STRIPE_SECRET_KEY']
    else:
        api_key = config['STRIPE_SECRET_KEY_TEST']

    #print 'api key = ',api_key
    return StripeClass(api_key)

def append_error(msg, err):
    #print "msg:{}, err:{}".format(msg,err)
    if not msg == '':
        msg += ', '
    return msg + err

#TODO: implement a function parameter parser

def get_created_after(no_of_days_ago):
    created_after = None
    if no_of_days_ago:
        d = (datetime.today() - timedelta(days=no_of_days_ago)).date()
        ut = int(round(time.mktime(d.timetuple())))
        created_after = {'gte':ut}
    return created_after

class StripeClass(object):
    INCORRECT_RANDOM_DEPOSIT_AMOUNTS_MSG = 'The amounts provided do not match the amounts that were sent to the bank account.'
    BANK_ALREADY_VERIFIED_MSG = 'This bank account has already been verified.'
    BANK_ALREADY_EXISTS_FOR_CUSTOMER_MSG = 'A bank account with that routing number and account number already exists for this customer.'
    def __init__(self, api_key):
        stripe.api_key = api_key
        self.LOGGER = logger.getLogger(__name__)

    def f(self, func):
        def stripe_call(*args, **kwargs):
            user_id = 'NOT_SET'
            try:
                if current_user:
                    user_id = current_user.get_id()

                return func(*args, **kwargs)
            except stripe.error.InvalidRequestError as e:
                stack = inspect.stack()
                self.LOGGER.error('from_function:{0} at_line:{1} type:{2} message:{3} user_id:{4}'.format(
                    stack[1][3],stack[1][2],e.__class__.__name__, e.message, user_id))
                if e.message == StripeClass.BANK_ALREADY_VERIFIED_MSG:
                    error.BankAlreadyVerifiedError(e.message, e)
                elif e.message == StripeClass.BANK_ALREADY_EXISTS_FOR_CUSTOMER_MSG:
                    error.BankAlreadyExistsError(e.message, e)
                else:
                    raise error.UserInputError(e.message, e.param, e)
            except stripe.error.CardError as e:
                stack = inspect.stack()
                self.LOGGER.error('from_function:{0} at_line:{1} type:{2} message:{3} user_id:{4}'.format(
                    stack[1][3],stack[1][2],e.__class__.__name__, e.message, user_id))
                if e.message == StripeClass.INCORRECT_RANDOM_DEPOSIT_AMOUNTS_MSG:
                    raise error.IncorrectRandomDepositAmountsError(e.message, e)
                else:
                    raise error.UserInputError(e.message, e.param, e)
            except Exception as e:
                stack = inspect.stack()
                self.LOGGER.exception('from_function:{0} at_line:{1} type:{2} message:{3} user_id:{4}'.format(
                    stack[1][3],stack[1][2],e.__class__.__name__, e.message, user_id))
                raise error.StripeError(constants.GENERIC_ERROR,e)
        return stripe_call

    def list_customers(self, created_in_last_days = 30, limit = 25, ending_before = None, starting_after = None):
        '''
            If we want to get all cutomers, i.e not default to 30 days back then set created_in_last_days = None during the call.
        '''
        return self.f(stripe.Customer.list)(created=get_created_after(created_in_last_days),limit=limit,ending_before=ending_before, \
                starting_after=starting_after,include=["total_count"])

    def create_customer(self, email):
        msg = ''
        if not email:
            msg = append_error(msg, 'email is required')
        if msg:
            raise ValueError(msg)
        """
            There is no API in Stripe to check if a customer already exists.
            The stripe cust_id has to be stored in local DB
        """
        return self.f(stripe.Customer.create)(metadata={'email':email})

    def get_customer(self, cust_id):
        msg = ''
        if not cust_id:
            msg = append_error(msg, 'cust_id is required')
        if msg:
            raise ValueError(msg)
        return self.f(stripe.Customer.retrieve)(cust_id)

    def delete_customer(self, cust_id):
        msg = ''
        if not cust_id:
            msg = append_error(msg, 'cust_id is required')
        if msg:
            raise ValueError(msg)
        cu = self.f(stripe.Customer.retrieve)(cust_id)
        self.f(cu.delete)
        return True

    def list_customer_banks(self, cust_id, limit = 25, ending_before = None, starting_after = None):
        msg = ''
        if not cust_id:
            msg = append_error(msg, 'cust_id is required')
        if msg:
            raise ValueError(msg)
        sources = self.f(stripe.Customer.retrieve)(cust_id).sources
        return self.f(sources.all)(object="bank_account", limit=limit,
            ending_before=ending_before, starting_after=starting_after)

    def get_customer_bank(self, cust_id, bank_id):
        msg = ''
        if not cust_id:
            msg = append_error(msg, 'cust_id is required')
        if not bank_id:
            msg = append_error(msg, 'bank_id is required')
        if msg:
            raise ValueError(msg)
        sources = self.f(stripe.Customer.retrieve)(cust_id).sources
        return self.f(sources.retrieve)(bank_id)

    def add_customer_bank(self, cust_id, token = None, account_number = None, country = None, \
            currency = None, routing_number = None, account_holder_name = None):
        msg = ''
        msg1 = ''
        if not cust_id:
            msg = append_error(msg, 'cust_id cannot be empty')

        if not token:
            #check that the bank parameters are present
            if not account_number:
                msg1 = append_error(msg1, "'acocunt_number' is required")
            if not country:
                msg1 = append_error(msg1, "'country' is required")
            if not currency:
                msg1 = append_error(msg1, "'currency' is required")
            if not routing_number:
                msg1 = append_error(msg1, "'routing_number' is required")
            if not account_holder_name:
                msg1 = append_error(msg1, "'account_holder_name' is required")
            if msg1:
                msg1 = "when 'token' is not present in the parameter list: " + msg1

        if msg or msg1:
            if msg1:
                msg = append_error(msg, msg1)
            raise ValueError(msg)

        #if 'set_default' in kwargs and kwargs['set_default']:
        #    set_default = True
        #else:
        #    set_default = False

        cu = self.f(stripe.Customer.retrieve)(cust_id)
        '''
            There is no API in stripe to check if the bank account is same before creating the bank account.
            Trying to add same bank account again gives a generic stripe.error.InvalidRequestError
        '''

        if not token:
            source = self.f(cu.sources.create)(source={'object':'bank_account',
                'account_holder_type':'individual',
                'account_number':account_number,
                'country':country,
                'currency':currency,
                'account_holder_name':account_holder_name,
                'routing_number':routing_number})
                #,default_for_currency=set_default)
        else:
            source = self.f(cu.sources.create)(source=token)

        return source

    def verify_customer_bank(self, cust_id, bank_id, f_amount, s_amount):
        msg = ''
        if not cust_id:
            msg = append_error(msg, 'cust_id is required')
        if not bank_id:
            msg = append_error(msg, 'bank_id is required')
        if not f_amount:
            msg = append_error(msg, 'f_amount is required')
        if not s_amount:
            msg = append_error(msg, 's_amount is required')
        if msg:
            raise ValueError(msg)
        cu = self.f(stripe.Customer.retrieve)(cust_id)
        bank = self.f(cu.sources.retrieve)(bank_id)
        return self.f(bank.verify)(amounts = [f_amount, s_amount])

    def delete_customer_bank(self, cust_id, bank_id):
        msg = ''
        if not cust_id:
            msg = append_error(msg, 'cust_id is required')
        if not bank_id:
            msg = append_error(msg, 'bank_id is required')
        if msg:
            raise ValueError(msg)
        cu = self.f(stripe.Customer.retrieve)(cust_id)
        bank = self.f(cu.sources.retrieve)(bank_id)
        return self.f(bank.delete)()

    def create_customer_charge(self, cust_id, bank_id, amount, currency, description = None):
        msg = ''
        if not cust_id:
            msg = append_error(msg, 'cust_id is required')
        if not amount:
            msg = append_error(msg, 'amount is required')
        if not currency:
            msg = append_error(msg, 'currency is required')
        if not bank_id:
            msg = append_error(msg, 'bank_id is required')
        if msg:
            raise ValueError(msg)

        func_args = {}
        func_args['customer'] = cust_id
        func_args['amount'] = amount
        func_args['currency'] = currency
        func_args['source'] = bank_id
        if description:
            func_args['description'] = description

        return stripe.Charge.create(**func_args)

    def get_charge(self, charge_id):
        msg = ''
        if charge_id == '':
            msg = append_error(msg, 'charge_id cannot be empty')
        if msg:
            raise ValueError(msg)
        return self.f(stripe.Charge.retrieve)(charge_id)

    def list_charges(self, cust_id=None, created_in_last_days = 30, limit = 25, ending_before = None, starting_after = None):
        '''
            If the cust_id = None, this will retrieve all the charges in this account
            If cust_id present, it will return charges for the specified customer.
        '''
        if not cust_id:
            return self.f(stripe.Charge.list)(created=get_created_after(created_in_last_days),limit=limit,ending_before=ending_before, \
                starting_after=starting_after,include=["total_count"])
        else:
            return self.f(stripe.Charge.list)(customer=cust_id,created=get_created_after(created_in_last_days),limit=limit,ending_before=ending_before, \
                starting_after=starting_after,include=["total_count"])
