import logging
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app, flash
from datetime import datetime
from application.db.model import User
from application.util.common import *
from application.services import mail
from application.util import constants
from forms import *

home_blueprint = Blueprint('home_blueprint', __name__)

@home_blueprint.route('/', methods=['GET'])
def index():
    return render_template('home/index-fiverr.html')

@home_blueprint.route('/623a6d00bc6b0c4e7c07136217ab2a8c.txt', methods=['GET'])
def email_verification():
    return ""

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
            to_email = request.form['email']
            name = request.form['name']
            user = User(name = name, email = to_email, time_created = datetime.now())
            current_app.db_session.add(user)
            current_app.db_session.commit()
            logging.info('Saved user %s' % to_email)
            mail.send(current_app.config['ADMIN_EMAIL'],
            to_email,
            constants.SIGNUP_EMAIL_SUBJECT,
            constants.SIGNUP_EMAIL_BODY)
            # send_mail(
            # to_email,
            # constants.SIGNUP_EMAIL_SUBJECT,
            # constants.SIGNUP_EMAIL_BODY)
            return jsonify(email=to_email)
        except Exception as e:
            logging.error('failed to save user, error = %s' % str(e))
            return jsonify(
                error='true',
                description=str(e))
    else:
        return jsonify(
            error='true',
            description='Only support POST request!')

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
