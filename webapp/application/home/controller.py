import logging
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app, flash, jsonify
from datetime import datetime, timedelta
from shared.db.model import User
from shared.services import mail
from shared.util import constants
from forms import *

home_blueprint = Blueprint('home_blueprint', __name__)

@home_blueprint.route('/', methods=['GET'])
def index():
    return render_template('home/index-fiverr.html')

@home_blueprint.route('/experiment-color', methods=['GET'])
def experiment_color():
    return render_template('home/index.html')

@home_blueprint.route('/register_user', methods=['POST'])
def register_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        # user = get_model().create(email)
        user = User(name = name, email = email, time_created = datetime.now())
        current_app.db_session.add(user)
        current_app.db_session.commit()
        return redirect(url_for('.index'))
    else:
        render_template('404.html')

@home_blueprint.route('/register_user_ajax', methods=['POST'])
def register_user_ajax():
    if request.method == 'POST':
        try:
            email = request.form['email']
            name = request.form['name']
            user = User(name = name, email = email, time_created = datetime.now())
            current_app.db_session.add(user)
            current_app.db_session.commit()
            logging.info('Saved user %s' % email)
            mail.send(current_app.config['ADMIN_EMAIL'],
            email,
            constants.SIGNUP_EMAIL_SUBJECT,
            constants.SIGNUP_EMAIL_BODY)
            return jsonify(email=email)
        except Exception as e:
            logging.error('failed to save user, error = %s' % str(e))
            return jsonify(
                error='true',
                description=str(e))
    else:
        return jsonify(
            error='true',
            description='Only support POST request!')

@home_blueprint.route('/get_payment_plan', methods=['POST'])
def get_payment_plan():
    loan_amount = float(request.form.get('loan_amount'))
    loan_duration = int(request.form.get('loan_duration'))

    result = {}
    result['summary'] = {}
    result['payment_schedule'] = {}
    result['summary']['loan_amount'] = loan_amount
    result['summary']['loan_duration'] = loan_duration
    min_apr = .36
    max_apr = .99

    start_time = datetime.now()

    min_payment = loan_amount + (loan_amount * min_apr * loan_duration) / 12
    max_payment = loan_amount + (loan_amount * max_apr * loan_duration) / 12
    monthly_payment_min = min_payment/loan_duration
    monthly_payment_max = max_payment/loan_duration
    expected_monthly_payment = (monthly_payment_min + monthly_payment_max) / 2

    result['summary']['min_payment'] = min_payment
    result['summary']['max_payment'] = max_payment
    result['summary']['min_apr'] = min_apr
    result['summary']['max_apr'] = max_apr
    result['summary']['min_interest'] = min_payment - loan_amount
    result['summary']['max_interest'] = max_payment - loan_amount
    result['summary']['monthly_payment_min'] = monthly_payment_min
    result['summary']['monthly_payment_max'] = monthly_payment_max
    result['summary']['expected_monthly_payment'] = expected_monthly_payment

    for t in range(loan_duration):
        result['payment_schedule'][t] = {
            'expected_amount': expected_monthly_payment,
            'date': start_time + timedelta(days=30)
        }

    return jsonify(result)

@home_blueprint.route('/contact_us', methods=['GET', 'POST'])
def contact_us():
    form = ContactUsForm()
    if form.validate_on_submit():
        message = '''Received email from {0}\n
        Subject: {1}\n
        Message: {2}'''.format(form.email.data, form.subject.data, form.message.data)

        mail.send(current_app.config['ADMIN_EMAIL'],
        current_app.config['ADMIN_EMAIL'],
        form.subject.data,
        message)
        flash('Thanks for contact us. We will get back to you as soon as possible.')
        return redirect(url_for('.index'))
    disable_production_mode = not current_app.config['ENABLE_PRODUCTION_MODE']
    return render_template('home/contact_us.html',
    disable_production_mode = disable_production_mode, form=form)
