from flask import current_app
import sendgrid
import os
from sendgrid.helpers.mail import *

def send(from_email, to_email, subject, message):
    sg = sendgrid.SendGridAPIClient(apikey=current_app.config['SENDGRID_API_KEY'])
    mail = Mail(Email(from_email), subject, Email(to_email), Content('text/html', message))
    response = sg.client.mail.send.post(request_body=mail.get())
    print(response.status_code)
    print(response.body)
    print(response.headers)
