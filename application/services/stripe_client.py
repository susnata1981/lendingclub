import stripe
from datetime import datetime, timedelta, date
import time
from flask import current_app

def init():
    current_app.stripe_client = init_standalone(current_app.config)

def init_standalone(config):
    api_key = 'test key'
    if config['ENABLE_PRODUCTION_MODE']:
        api_key = config['STRIPE_SECRET_KEY']
    else:
        api_key = config['STRIPE_SECRET_KEY_TEST']

    print 'api key = ',api_key
    return StripeClass(api_key)

def append_error(msg, err):
    #print "msg:{}, err:{}".format(msg,err)
    if not msg == '':
        msg += ', '
    return msg + err

#TODO: implement a function parameter parser

class StripeClass(object):
    def __init__(self, api_key):
        stripe.api_key = api_key

    def list_customers(self, **kwargs):
        days_to_subtract = None
        if kwargs is not None:
            if 'since_days_ago' in kwargs:
                days_to_subtract = kwargs['since_days_ago']
        if days_to_subtract is None:
            days_to_subtract = 30

        d = (datetime.today() - timedelta(days=days_to_subtract)).date()
        ut = int(round(time.mktime(d.timetuple())))

        return stripe.Customer.list(created={'gte':ut})

    def create_customer(self, f_name, l_name, address):
        msg = ''
        if f_name == '':
            msg = append_error(msg, 'f_name cannot be empty')
        if l_name == '':
            msg = append_error(msg, 'l_name cannot be empty')
        if address == '':
            msg = append_error(msg, 'address cannot be empty')
        if not msg == '':
            raise ValueError(msg)

        local_name = f_name + ' ' + l_name
        """
            There is no API in Stripe to check if a customer already exists.
            The stripe cust_id has to be stored in local DB
        """
        cu = stripe.Customer.create(shipping={'name':local_name,'address':{'line1':address}})
        return cu

    def get_customer(self, cust_id):
        msg = ''
        if cust_id == '':
            msg = append_error(msg, 'cust_id cannot be empty')
        if not msg == '':
            raise ValueError(msg)

        return stripe.Customer.retrieve(cust_id)

    def delete_customer(self, cust_id):
        msg = ''
        if cust_id == '':
            msg = append_error(msg, 'cust_id cannot be empty')
        if not msg == '':
            raise ValueError(msg)
        stripe.Customer.retrieve(cust_id).delete()
        return True

    def list_customer_banks(self, cust_id):
        msg = ''
        if cust_id == '':
            msg = append_error(msg, 'cust_id cannot be empty')
        if not msg == '':
            raise ValueError(msg)
        return stripe.Customer.retrieve(cust_id).sources.all(object="bank_account")

    def get_customer_bank(self, cust_id, bank_id):
        pass

    def add_customer_bank(self, cust_id, **kwargs):
        msg = ''
        if cust_id == '':
            msg = append_error(msg, 'cust_id cannot be empty')

        if 'token' not in kwargs:
            #check that the bank parameters are present
            msg1 = ''
            if 'account_number' not in kwargs:
                msg1 = append_error(msg1, "'acocunt_number' is required")
            if 'country' not in kwargs:
                msg1 = append_error(msg1, "'country' is required")
            if 'currency' not in kwargs:
                msg1 = append_error(msg1, "'currency' is required")
            if 'routing_number' not in kwargs:
                msg1 = append_error(msg1, "'routing_number' is required")
            if 'account_holder_name' not in kwargs:
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

        cu = stripe.Customer.retrieve(cust_id)
        '''
            There is no API in stripe check if the bank account is same before creating the bank account.
            Trying to add same bank account again gives a generic stripe.error.InvalidRequestError
        '''

        if 'token' not in kwargs :
            source = cu.sources.create(source={'object':'bank_account',
                'account_holder_type':'individual',
                'account_number':kwargs['account_number'],
                'country':kwargs['country'],
                'currency':kwargs['currency'],
                'account_holder_name':kwargs['account_holder_name'],
                'routing_number':kwargs['routing_number']})
                #,default_for_currency=set_default)
        else:
            source = cu.sources.create(source=kwargs['token'])
        return source

    def verify_customer_bank(self, cust_id, bank_id, f_amount, s_amount):
        msg = ''
        if cust_id == '':
            msg = append_error(msg, 'cust_id cannot be empty')
        if bank_id == '':
            msg = append_error(msg, 'bank_id cannot be empty')
        if f_amount == '':
            msg = append_error(msg, 'f_amount cannot be empty')
        if s_amount == '':
            msg = append_error(msg, 's_amount cannot be empty')
        if msg:
            raise ValueError(msg)
        cu = stripe.Customer.retrieve(cust_id)
        bank_account = cu.sources.retrieve(bank_id)
        return bank_account.verify(amounts = [f_amount, s_amount])

    def delete_customer_bank(self, cust_id, bank_id):
        msg = ''
        if cust_id == '':
            msg = append_error(msg, 'cust_id cannot be empty')
        if bank_id == '':
            msg = append_error(msg, 'bank_id cannot be empty')
        if msg:
            raise ValueError(msg)
        return stripe.Customer.retrieve(cust_id).sources.retrieve(bank_id).delete()

    def list_customer_charges(self, cust_id):
        msg = ''
        if cust_id == '':
            msg = append_error(msg, 'cust_id cannot be empty')
        if msg:
            raise ValueError(msg)
        return stripe.Charge.list(customer=cust_id)

    def create_customer_charge(self, cust_id, amount, currency, **kwargs):
        msg = ''
        if cust_id == '':
            msg = append_error(msg, 'cust_id cannot be empty')
        if amount == '':
            msg = append_error(msg, 'amount cannot be empty')
        if currency == '':
            msg = append_error(msg, 'currency cannot be empty')
        if msg:
            raise ValueError(msg)
        bank_id = ''
        if 'bank_id' in kwargs and kwargs['bank_id'] != '':
            bank_id = kwargs['bank_id']

        if bank_id == '':
            return stripe.Charge.create(
                amount=amount,
                currency=currency,
                customer=cust_id)
        else:
            return stripe.Charge.create(
                amount=amount,
                currency=currency,
                customer=cust_id,
                source=bank_id)

    def get_customer_charge(self, cust_id, charge_id):
        msg = ''
        if cust_id == '':
            msg = append_error(msg, 'cust_id cannot be empty')
        if charge_id == '':
            msg = append_error(msg, 'charge_id cannot be empty')
        if msg:
            raise ValueError(msg)
        #TODO: Check that the charge belongfs to the customer
        return stripe.Charge.retrieve(charge_id)
