import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'util'))

import config_loader, stripe_client, argparse

CLIENT = None
LOGGER = logger.getLogger('stripe_wrapper')

def list_customers(args):
    func_args = {}
    if args.created_in_last_days == -2:
        func_args['created_in_last_days'] = None
    elif args.created_in_last_days > -1:
        func_args['created_in_last_days'] = args.created_in_last_days

    if args.limit == -2:
        func_args['limit']=None
    elif args.limit > -1:
        func_args['limit'] = args.limit

    if args.ending_before != '-1':
        func_args['ending_before'] = args.ending_before

    if args.starting_after != '-1':
        func_args['starting_after'] = args.starting_after

    print CLIENT.list_customers(**func_args)

def create_customer(args):
    print CLIENT.create_customer(args.ph_no)

def get_customer(args):
    print CLIENT.get_customer(args.cust_id)

def delete_customer(args):
    print CLIENT.delete_customer(args.cust_id)

def list_customer_banks(args):
    func_args = {}

    func_args['cust_id'] = args.cust_id
    if args.limit == -2:
        func_args['limit']=None
    elif args.limit > -1:
        func_args['limit'] = args.limit

    if args.ending_before != '-1':
        func_args['ending_before'] = args.ending_before

    if args.starting_after != '-1':
        func_args['starting_after'] = args.starting_after

    print CLIENT.list_customer_banks(**func_args)

def get_customer_bank(args):
    print CLIENT.get_customer_bank(args.cust_id, args.bank_id)

def add_customer_bank(args):
    func_args = {}
    func_args['cust_id'] = args.cust_id
    func_args['account_number'] = args.account_number
    func_args['country'] = args.country
    func_args['currency'] = args.currency
    func_args['routing_number'] = args.routing_number
    func_args['account_holder_name'] = args.account_holder_name
    if args.token != '-1':
        func_args['token'] = args.token

    try:
        print CLIENT.add_customer_bank(**func_args)
    except Exception as e:
        LOGGER.exception(e.message)

def delete_customer_bank(args):
    print CLIENT.delete_customer_bank(args.cust_id, args.bank_id)

def verify_customer_bank(args):
    print CLIENT.verify_customer_bank(args.cust_id, args.bank_id, args.f_amount, args.s_amount)

def create_customer_charge(args):
    print CLIENT.create_customer_charge(args.cust_id, args.bank_id, args.amount, args.currency, args.description)

def get_charge(args):
    print CLIENT.get_charge(args.charge_id)

def list_charges(args):
    func_args = {}
    if args.cust_id != '-1':
        func_args['cust_id'] = args.cust_id

    if args.created_in_last_days == -2:
        func_args['created_in_last_days'] = None
    elif args.created_in_last_days > -1:
        func_args['created_in_last_days'] = args.created_in_last_days

    if args.limit == -2:
        func_args['limit']=None
    elif args.limit > -1:
        func_args['limit'] = args.limit

    if args.ending_before != '-1':
        func_args['ending_before'] = args.ending_before

    if args.starting_after != '-1':
        func_args['starting_after'] = args.starting_after

    print CLIENT.list_charges(**func_args)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='subcommands', help='additional help')

    parser_lc = subparsers.add_parser('list-customers', help='list Stripe customers')
    parser_lc.add_argument('created_in_last_days', type=int,
        help='eg: specify 30 to list customers created in the last 30 days. To use the function parameter default specify -1. To retrieve all customers irrespective of create date specify -2')
    parser_lc.add_argument('limit', type=int,
        help='eg: specify 20 to list only 20 customers. To use the function parameter default specify -1. To retrieve the Stripe default list of 10 customers specify -2')
    parser_lc.add_argument('ending_before', nargs='?', default='-1',
        help='A cursor for use in pagination. ending_before is an object ID that defines your place in the list. If not soecified, defaults to -1')
    parser_lc.add_argument('starting_after', nargs='?', default='-1',
        help='A cursor for use in pagination. starting_after is an object ID that defines your place in the list. If not soecified, defaults to -1 ')
    parser_lc.set_defaults(func=list_customers)

    parser_cc = subparsers.add_parser('create-customer', help='Create new Stripe customer')
    parser_cc.add_argument('ph_no', help='Phone number to identify the created Stripe customer.')
    parser_cc.set_defaults(func=create_customer)

    parser_gc = subparsers.add_parser('get-customer', help='Get Stripe customer')
    parser_gc.add_argument('cust_id', help='Stripe customer id to get details for.')
    parser_gc.set_defaults(func=get_customer)

    parser_dc = subparsers.add_parser('delete-customer', help='Delete Stripe customer')
    parser_dc.add_argument('cust_id', help='Stripe customer id to be delted.')
    parser_dc.set_defaults(func=delete_customer)

    parser_lcb = subparsers.add_parser('list-customer-banks', help='list the Stripe customer banks.')
    parser_lcb.add_argument('cust_id', help='Stripe customer id to get details for.')
    parser_lcb.add_argument('limit', type=int,
        help='eg: specify 20 to list only 20 banks for this customer. To use the function parameter defaults specify -1. To retrieve the Stripe default list of at most 10 customer banks, specify -2')
    parser_lcb.add_argument('ending_before', nargs='?', default='-1',
        help='A cursor for use in pagination. ending_before is an object ID that defines your place in the list. If not soecified, defaults to -1')
    parser_lcb.add_argument('starting_after', nargs='?', default='-1',
        help='A cursor for use in pagination. starting_after is an object ID that defines your place in the list. If not soecified, defaults to -1')
    parser_lcb.set_defaults(func=list_customer_banks)

    parser_gcb = subparsers.add_parser('get-customer-bank', help='Get Stripe customer bank')
    parser_gcb.add_argument('cust_id', help='Stripe customer id to get details for.')
    parser_gcb.add_argument('bank_id', help='Stripe customer bank id to get details for.')
    parser_gcb.set_defaults(func=get_customer_bank)

    parser_acb = subparsers.add_parser('add-customer-bank', help='Get Stripe customer')
    parser_acb.add_argument('cust_id', help='Stripe customer id to which the bank needs to be added.')
    parser_acb.add_argument('token', help='Stripe bank token. To use the function parameter defaults specify -1')
    parser_acb.add_argument('account_number', nargs='?', default=None, help='bank account number(required when token to specified).')
    parser_acb.add_argument('country', nargs='?', default=None, help='bank account country(required when token to specified).')
    parser_acb.add_argument('currency', nargs='?', default=None, help='bank account currency(required when token to specified).')
    parser_acb.add_argument('routing_number', nargs='?', default=None, help='bank account routing number(required when token to specified).')
    parser_acb.add_argument('account_holder_name', nargs='?', default=None, help='bank account account holder name(required when token to specified).')
    parser_acb.set_defaults(func=add_customer_bank)

    parser_vcb = subparsers.add_parser('verify-customer-bank', help='Verify Stripe customer bank')
    parser_vcb.add_argument('cust_id', help='Stripe customer id.')
    parser_vcb.add_argument('bank_id', help='Stripe customer bank id.')
    parser_vcb.add_argument('f_amount', help='first amount')
    parser_vcb.add_argument('s_amount', help='second amount')
    parser_vcb.set_defaults(func=verify_customer_bank)

    parser_dcb = subparsers.add_parser('delete-customer-bank', help='Delete Stripe customer bank')
    parser_dcb.add_argument('cust_id', help='Stripe customer id.')
    parser_dcb.add_argument('bank_id', help='Stripe customer bank id.')
    parser_dcb.set_defaults(func=delete_customer_bank)

    parser_ccb = subparsers.add_parser('create-customer-charge', help='Charge a Stripe customer bank')
    parser_ccb.add_argument('cust_id', help='Stripe customer id.')
    parser_ccb.add_argument('bank_id', help='Stripe customer bank id.')
    parser_ccb.add_argument('amount', help='charge amount (no decimals, i.e 1 dollar = 100)')
    parser_ccb.add_argument('currency', help='3 letter currency code eg: USD')
    parser_ccb.add_argument('description', default = None, help='Charge description -- like Membership or Interest')
    parser_ccb.set_defaults(func=create_customer_charge)

    parser_gcharge = subparsers.add_parser('get-charge', help='Get Stripe charge details')
    parser_gcharge.add_argument('charge_id', help='Stripe charge id to get details for.')
    parser_gcharge.set_defaults(func=get_charge)

    parser_list_charges = subparsers.add_parser('list-charges', help='list Stripe charges')
    parser_list_charges.add_argument('cust_id', help='Stripe customer id.To use the function parameter defaults specify -1')
    parser_list_charges.add_argument('created_in_last_days', type=int,
        help='eg: specify 30 to list charges created in the last 30 days. To use the function parameter defaults specify -1. To retrieve all charges irrespective of create date specify -2')
    parser_list_charges.add_argument('limit', type=int,
        help='eg: specify 20 to list only 20 charges . To use the function parameter defaults specify -1. To retrieve the Stripe default list of at most 10 charges, specify -2')
    parser_list_charges.add_argument('ending_before', nargs='?', default='-1',
        help='A cursor for use in pagination. ending_before is an object ID that defines your place in the list.')
    parser_list_charges.add_argument('starting_after', nargs='?', default='-1',
        help='A cursor for use in pagination. starting_after is an object ID that defines your place in the list.')
    parser_list_charges.set_defaults(func=list_charges)

    args = parser.parse_args()

    config_path = os.path.join(os.path.dirname(__file__), '..', '..','config.py')
    CLIENT = stripe_client.init_standalone(config_loader.load_config(config_path))
    args.func(args)

    '''
    #failure on use
    print client.add_customer_bank('cus_9Apk1sAvWFDXKP',
        routing_number='110000000',
        account_number='000111111116',
        country='US',
        currency='USD',
        account_holder_name='testy1 tester',
        set_default=True)


    #success on use
    print client.add_customer_bank('cus_9Apk1sAvWFDXKP',
        routing_number='110000000',
        account_number='000123456789',
        country='US',
        currency='USD',
        account_holder_name='testy1 tester',
        set_default=True)
    '''

#python stripe_wrapper.py add-customer-bank cus_9JY2j87VJHVqD5 -1 000111111116 US USD 110000000 'testy1 tester'
#- Adding same bank to a customer : stripe.error.InvalidRequestError: Request req_9K0HroCGGQxl4O: A bank account with that routing number and account number already exists for this customer.
#- Invalid routing number (!= 9 digits) : stripe.error.InvalidRequestError: Request req_9K7JETyGSLqbHH: Routing number must have 9 digits
#- Incorrect routing number : stripe.error.InvalidRequestError: Request req_9K7L7CZ7QHcGOL: Invalid routing number
