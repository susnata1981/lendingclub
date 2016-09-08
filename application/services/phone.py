from twilio.rest import TwilioRestClient
from flask import current_app

def init():
    client = TwilioRestClient(
        current_app.config['TWILIO_ACCOUNT_SID'],
        current_app.config['TWILIO_ACCOUNT_TOKEN'])
    current_app.phone_client = client

def send_message(to, body):
    current_app.phone_client.messages.create(
    to = to, from_ = current_app.config['TWILIO_PHONE_NUMBER'], body = body)
