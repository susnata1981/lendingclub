from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify
from shared.services import stripe_client
from forms import *
from shared.db.model import *
import traceback
import random
from datetime import datetime
from flask.ext.login import current_user, login_required, login_user, logout_user
from shared.util import constants, error
from shared import services
from shared.bli import account as accountBLI
from pprint import pprint
import json
import logging
import dateutil
from dateutil.relativedelta import relativedelta
from shared.bli import bank as bankBLI
from shared.bli.viewmodel.bank_data import *
from application.onboarding.forms import ResendEmailVerificationForm

account_bp = Blueprint('account_bp', __name__, url_prefix='/account')

@account_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        try:
            account = accountBLI.verify_login(form.email.data, form.password.data)
            login_user(account)
            next = request.args.get('next')
            # next_is_valid should check if the user has valid
            # permission to access the `next` url
            # print 'Next page =',next,' is_valid_next =',next_is_valid(next)
            # if not next_is_valid(next):
            #     return flask.abort(404)
            return redirect(next or url_for('lending_bp.dashboard'))
        except error.DatabaseError as de:
            print 'Database error:',de.orig_exp.message
            flash(constants.GENERIC_ERROR)
            return render_template('account/login.html', form=form)
        except error.InvalidLoginCredentialsError:
            # print 'Invalid credentials'
            flash(constants.INVALID_CREDENTIALS)
            return render_template('account/login.html', form=form)
        except error.EmailVerificationRequiredError:
            # print 'Email verification required'
            flash(constants.ACCOUNT_NOT_VERIFIED)
            # verify email message
            data = {}
            data['email_verification_required'] = True
            email_form = ResendEmailVerificationForm(request.form)
            return render_template('onboarding/verify_email.html', data=data, form=email_form)
        except Exception as e:
            print 'Exception::',e
            print traceback.format_exc()
            return render_template('404.html')
    return render_template('account/login.html', form=form)

@account_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('.login'))

@account_bp.route('/profile', methods=['GET'])
@login_required
def account():
    data = {}
    return render_template('account/account.html', data=data)

@account_bp.route('/reset_password', methods=['GET','POST'])
def reset_password():
    form = ResetPasswordForm(request.form)
    data = {}
    if form.validate_on_submit():
        email = form.email.data
        try:
            account = get_account_by_email(email)
            if not account:
                flash('Account for this email(%s) doesn\'t exist at Ziplly.' % (email))
            else:
                try:
                    accountBLI.initiate_reset_password(account)
                    data['email_sent'] = True
                except error.MailServiceError:
                    flash(constants.RESET_PASSWORD_EMAIL_SEND_FAILURE_MESSAGE)
        except Exception:
            flash(constants.GENERIC_ERROR)
    return render_template('account/reset_password.html', data=data, form=form)

@account_bp.route('/<id>/reset_password', methods=['GET','POST'])
def reset_password_verify(id):
    token = request.args.get(constants.VERIFICATION_TOKEN_NAME)
    account = None
    try:
        account = accountBLI.verify_password_reset(int(id), token)
    except error.DatabaseError as de:
        logging.error('ERROR: Database Exception: %s' % (de.message))
        flash(constants.GENERIC_ERROR)
    except Exception as e:
        logging.error(e.message)
    if account:
        session['password_account_id'] = account.id
    return redirect(url_for('.reset_password_confirm'))

@account_bp.route('/reset_password_confirm', methods=['GET','POST'])
def reset_password_confirm():
    logging.info('reset_password_confirm entry')
    form = ResetPasswordConfirmForm(request.form)
    data = {}
    if not 'password_account_id' in session or not session['password_account_id']:
        data['unauthorized'] = True
    elif form.validate_on_submit():
        account = get_account_by_id(session['password_account_id'])
        try:
            accountBLI.reset_password(account, form.password.data)
            session.pop('password_account_id', None)
            login_user(account)
            logging.info('reset_password_confirm - redirect exit')
            return redirect(url_for('lending_bp.dashboard'))
        except error.DatabaseError as de:
            print 'ERROR: Database Exception: %s' % (de.message)
            flash(constants.GENERIC_ERROR)
    logging.info('reset_password_confirm exit')
    return render_template('account/reset_password_confirm.html', data=data, form=form)
