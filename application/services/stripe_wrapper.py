import sys, os, stripe_client

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import config

if __name__ == '__main__':
    config_dict = dict([('ENABLE_PRODUCTION_MODE', config.ENABLE_PRODUCTION_MODE),
       ('STRIPE_SECRET_KEY', config.STRIPE_SECRET_KEY),
       ('STRIPE_SECRET_KEY_TEST', config.STRIPE_SECRET_KEY_TEST)])
    client = stripe_client.init_standalone(config_dict)

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
