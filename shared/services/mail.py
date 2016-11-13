from flask import current_app

# import sendgrid
# import os
# from sendgrid.helpers.mail import *
#
# def send(from_email, to_email, subject, message):
#     sg = sendgrid.SendGridAPIClient(apikey=current_app.config['SENDGRID_API_KEY'])
#     mail = Mail(Email(from_email), subject, Email(to_email), Content('text/html', message))
#     response = sg.client.mail.send.post(request_body=mail.get())
#     print(response.status_code)
#     print(response.body)
#     print(response.headers)

from mailjet_rest import Client
import os
from shared.util import logger

LOGGER = logger.getLogger('shared.service.mail')

def send(from_email, to_email, subject, message, html_message=None):
    api_key = current_app.config['MJ_APIKEY_PUBLIC']
    api_secret = current_app.config['MJ_APIKEY_PRIVATE']
    mailjet = Client(auth=(api_key, api_secret))
    if not html_message:
        html_message = message
    data = {
        'FromEmail': from_email,
        'FromName': current_app.config['ADMIN_NAME'],
        'Subject': subject,
        'Text-part': message,
        'Html-part': html_message,
        'Recipients': [{'Email':to_email}]
    }
    result = mailjet.send.create(data=data)
    LOGGER.info('send email to %s, status %d, result %s' % (to_email, result.status_code, result))
