import os
import sys
from flask import current_app, flash
import logging
import random
import string
import traceback
import re
from shared.bli.viewmodel.notification import Notification

def PhoneNumberValidator():
    patt = re.compile('\d{3}-\d{3}-\d{4}')
    message = 'Invalid phone number format (xxx-xxx-xxxx)'

    def validator(form, field):
        if not patt.match(field.data):
            raise ValidationError(message)
    return validator

def SSNValidator():
    message = 'Invalid SSN format (xxx-xx-xxxx)'
    ssn_pattern = re.compile('\d{3}-\d{2}-\d{4}')

    def validator(form, field):
        if not ssn_pattern.match(field.data):
            raise ValidationError(message)
    return validator

def is_running_on_app_engine():
    '''Returns true if the application is running on app engine. Keep in
    mind that applcation can be in test mode even though it might be running
    on app engine. For that you need to use the ENABLE_PRODUCTION_MODE config
    flag.'''
    env = os.getenv('SERVER_SOFTWARE')
    # print 'ENVIRONMENT  = %s' % env
    if (env and env.startswith('Google App Engine/')):
        return True
    return False

def get_url_root():
    if is_running_on_app_engine():
        return 'http://www.ziplly.com'
    else:
        return 'http://localhost:8080'

def generate_fake_token(n):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(n))

def send_mail(to, subject, body):
    # import google
    # sys.path.insert(0, google.__path__.append(
    # '/Users/susnata/Project/NewVentures/PaydayLoan/lendingclub/env/lib/python2.7/site-packages/google_appengine/google'))
    if not is_running_on_app_engine():
        logging.info('running in localhost, skipping email.')
        return

    try:
        from google.appengine.api import mail
    except Exception as e:
        logging.error('Failed to import mail api ',e)

    message = mail.EmailMessage(
    sender = current_app.config['ADMIN_EMAIL'],
    subject = subject,
    to = to)
    message.body = body
    message.html = "<html><body>"+body+"</body></html>"
    logging.info('Sending message to %s, from %s, subject %s, body %s'
    % (to, current_app.config['ADMIN_EMAIL'], subject, body))
    try:
        message.send()
    except Exception as e:
        traceback.print_exc()
        logging.error('message.send() failed')

def get_notification(message, type):
    return Notification(title=message, notification_type=type)

def flash_error(message):
    flash(get_notification(message, Notification.ERROR).to_map())

def flash_success(message):
    flash(get_notification(message, Notification.SUCCESS).to_map())
