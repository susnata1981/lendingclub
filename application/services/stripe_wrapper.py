import sys, os, stripe_client

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import config

COMMENT_CHAR = '#'
OPTION_CHAR =  '='
MULTI_LINE_COMMENT_STR_1 = "'''"
MULTI_LINE_COMMENT_STR_2 = '"""'

#NOTE:
#this config loader has following limitations
#   multiline comment identifier should be the first string seq. in a line to indicate start
#   multiline comment identifier should be the last string seq in a line to indicate end

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', '..','config.py')
    options = {}
    with open(config_path, 'r') as my_config:
        imy_config = iter(my_config)
        for line in imy_config:
            #handle multiline comments
            MULTI_LINE_COMMENT_1_SET = False
            MULTI_LINE_COMMENT_2_SET = False
            if MULTI_LINE_COMMENT_1_SET and not (line.startswith(MULTI_LINE_COMMENT_STR_1) or line.endswith(MULTI_LINE_COMMENT_STR_1)):
                continue
            if MULTI_LINE_COMMENT_2_SET and not (line.startswith(MULTI_LINE_COMMENT_STR_2) or line.endswith(MULTI_LINE_COMMENT_STR_2)):
                continue
            if not MULTI_LINE_COMMENT_2_SET and (line.startswith(MULTI_LINE_COMMENT_STR_1) or line.endswith(MULTI_LINE_COMMENT_STR_1)):
                MULTI_LINE_COMMENT_1_SET = not MULTI_LINE_COMMENT_1_SET
                continue
            if not MULTI_LINE_COMMENT_1_SET and (line.startswith(MULTI_LINE_COMMENT_STR_2) or line.endswith(MULTI_LINE_COMMENT_STR_2)):
                MULTI_LINE_COMMENT_2_SET = not MULTI_LINE_COMMENT_2_SET
                continue

            # First, remove comments:
            if COMMENT_CHAR in line:
                # split on comment char, keep only the part before
                line, comment = line.split(COMMENT_CHAR, 1)
            # Second, find lines with an option=value:
            if OPTION_CHAR in line:
                # split on option char:
                option, value = line.split(OPTION_CHAR, 1)
                # strip spaces
                option = option.strip()
                # strip spaces, new lines and quotes
                value = value.strip(' \'"\n')
                while value.endswith('\\'):
                    value = value.strip(' \'"\n\\') + next(imy_config).strip(' \'"\n')

                # store in dictionary:
                options[option] = value
    return options

if __name__ == '__main__':
    #print load_config()
    # config_dict = dict([('ENABLE_PRODUCTION_MODE', config.ENABLE_PRODUCTION_MODE),
    #    ('STRIPE_SECRET_KEY', config.STRIPE_SECRET_KEY),
    #    ('STRIPE_SECRET_KEY_TEST', config.STRIPE_SECRET_KEY_TEST)])
    # client = stripe_client.init_standalone(config_dict)
    client = stripe_client.init_standalone(load_config())

    #TODO: use arg processor for command line arguments

    print client.list_customers()
    #print client.delete_customer('cus_9AnuicdPtqBeRX')
    #print client.create_customer('testy4','tester','test lane 4')
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
    #print client.delete_customer_bank('cus_9AnuicdPtqBeRX','ba_18sT4tBzxLgV0SlFW9PGkCiV')
    #print client.verify_customer_bank('cus_9AnuicdPtqBeRX', 'ba_18sTo3BzxLgV0SlFepI6ZDHF', 32, 45)
    #print client.create_customer_charge('cus_9AnuicdPtqBeRX',1500, 'USD', bank_id='ba_18sTo3BzxLgV0SlFepI6ZDHF')
    #print client.list_customer_charges('cus_9AnuicdPtqBeRX')
    #print client.get_customer('cus_9AnuicdPtqBeRX')
