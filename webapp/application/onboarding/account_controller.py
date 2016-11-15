from flask import Blueprint, render_template, session, request, redirect, url_for, flash, jsonify
from plaid import Client
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
import requests
import json
import logging
import dateutil
from dateutil.relativedelta import relativedelta

account_bp = Blueprint('account_bp', __name__, url_prefix='/account')

def generate_and_store_new_verification_code(account):
    # verification_code = random.randint(1000, 9999)
    verification_code = 1111
    account.phone_verification_code = verification_code
    current_app.db_session.add(account)
    current_app.db_session.commit()
    return verification_code

@account_bp.route('/verify/resend', methods=['GET', 'POST'])
def resend_email_verification():
    form = ResendEmailVerificationForm(request.form)
    data = {}
    if form.validate_on_submit():
        email = form.email.data
        try:
            account = get_account_by_email(email)
            if not account:
                flash('Account for this email(%s) doesn\'t exist at Ziplly.' % (email))
                data['show_email_verification_form'] = True
            elif accountBLI.is_email_verified(account):
                flash('Email already verified.')
                data['email_already_verified'] = True
            else:
                try:
                    accountBLI.initiate_email_verification(account)
                    data['email_sent'] = True
                except error.EmailVerificationSendingError:
                    flash(constants.EMAIL_VERIFICATION_SEND_FAILURE_MESSAGE)
                    data['show_email_verification_form'] = True
        except Exception:
            flash(constants.GENERIC_ERROR)

            data['show_email_verification_form'] = True
    else:
        data['show_email_verification_form'] = True
    return render_template('onboarding/verify_email.html', data=data, form=form)

@account_bp.route('/<id>/verify', methods=['GET'])
def verify_email(id):
    form = ResendEmailVerificationForm(request.form)
    token = request.args.get(constants.EMAIL_VERIFICATION_TOKEN_NAME)
    data = {}
    try:
        accountBLI.verify_email(int(id), token)
        return redirect(url_for('account_bp.account_verified'))
    except (error.AccountNotFoundError, error.EmailVerificationNotMatchError) as e:
        flash('Invalid verification code.')
        data['show_email_verification_form'] = True
    except error.AccountEmailAlreadyVerifiedError:
        flash('Email already verified.')
        data['email_already_verified'] = True
    except error.DatabaseError:
        flash(constants.GENERIC_ERROR)
        data['show_email_verification_form'] = True
    return render_template('onboarding/verify_email.html', data=data, form=form)

@account_bp.route('/verify', methods=['GET', 'POST'])
def verify_phone_number():
    form = PhoneVerificationForm(request.form)
    if form.validate_on_submit():
        account = get_account_by_id(session['account_id'])
        if account.status == int(Account.UNVERIFIED) and \
        form.verification_code.data == account.phone_verification_code:
            account.status = Account.VERIFIED_PHONE

            stripe_customer = current_app.stripe_client.create_customer(
            account.phone_number)

            account.stripe_customer_id = stripe_customer['id']
            account.time_updated = datetime.now()
            current_app.db_session.add(account)
            current_app.db_session.commit()
            return redirect(url_for('account_bp.account_verified'))
        else:
            flash('Invalid verification code')
    return render_template('onboarding/verify.html', form=form)

@account_bp.route('/account_verified', methods=['GET'])
def account_verified():
    return render_template('onboarding/account_verified.html')

# ajax
@account_bp.route('/resend_verification', methods=['POST'])
def resend_verification():
    if session['account_id'] is None:
        return jsonify({
            'error': True,
            'description': constants.MISSING_ACCOUNT
        })
    try:
        account = get_account_by_id(session['account_id'])
        verification_code = generate_and_store_new_verification_code(account)
        target_phone = '+1' + account.phone_number
        # services.phone.send_message(target_phone, constants.PHONE_VERIFICATION_MSG.format(verification_code))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({
            'error': True,
            'description': traceback.print_exc()
        })

@account_bp.route('/', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('.account'))

    form = SignupForm(request.form)
    print 'errors - ',form.errors
    if form.validate_on_submit():
        try:
            now = datetime.now()
            account = Account(
               first_name = form.first_name.data,
               last_name = form.last_name.data,
               phone_number = form.phone_number.data,
               email = form.email.data,
               dob = form.dob.data,
               ssn = form.ssn.data,
               promotion_code = form.promotion_code.data,
               password = form.password.data,
               time_created = now,
               time_updated = now)

            address = Address(
                street1 = form.street1.data,
                street2 = form.street2.data,
                city = form.city.data,
                state = form.state.data,
                postal_code = form.postal_code.data,
                address_type = Address.EMPLOYER,
               time_created = now,
               time_updated = now)

            account.addresses.append(address)

            accountBLI.signup(account)
        except error.AccountExistsError:
            flash(constants.ACCOUNT_WITH_EMAIL_ALREADT_EXISTS)
            return render_template('onboarding/signup.html', form=form)
        except error.EmailVerificationSendingError:
            flash(constants.ACCOUNT_CREATED_BUT_EMAIL_VERIFICATION_SEND_FAILURE_MESSAGE)
            data = {}
            data['show_email_verification_form'] = True
            email_form = ResendEmailVerificationForm(request.form)
            return render_template('onboarding/verify_email.html', data=data, form=email_form)
        except error.DatabaseError as de:
            print 'ERROR: Database Exception: %s' % (de.message)
            flash(constants.GENERIC_ERROR)
            return render_template('onboarding/signup.html', form=form)
        except Exception as e:
            print 'ERROR: General Exception: %s' % (e.message)
            flash(constants.GENERIC_ERROR)
            return render_template('onboarding/signup.html', form=form)

        # verify email message
        data = {}
        data['email_sent'] = True
        email_form = ResendEmailVerificationForm(request.form)
        return render_template('onboarding/verify_email.html', data=data, form=email_form)

    return render_template('onboarding/signup.html', form=form)


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
            return render_template('onboarding/login.html', form=form)
        except error.InvalidLoginCredentialsError:
            # print 'Invalid credentials'
            flash(constants.INVALID_CREDENTIALS)
            return render_template('onboarding/login.html', form=form)
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
    return render_template('onboarding/login.html', form=form)

def fetch_financial_information():
    for fi in current_user.fis:
        response = get_bank_info(fi.bank_account_id)
        fi.available_balance = response['available_balance']
        fi.current_balance = response['current_balance']
        fi.subtype = response['subtype']
        fi.subtype_name = response['subtype_name']
        fi.account_number_last_4 = response['account_number_last_4']
        fi.institution_type = response['institution_type']

@account_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('.login'))

@account_bp.route('/home', methods=['GET'])
@login_required
def account():
    if current_user.status != Account.VERIFIED_PHONE:
        flash({
            'content':'Please verify your phone first',
            'class': 'error'
        })
        return redirect(url_for('.verify_phone_number'))

    data = {}
    eligible_for_membership_reapplication = True
    for membership in current_user.memberships:
        if membership.is_active() or membership.is_pending():
            eligible_for_membership_reapplication = False
    data['eligible_for_membership_reapplication'] = eligible_for_membership_reapplication

    if len(current_user.memberships) == 0:
        data['show_notification'] = True
        data['notification_message'] = 'You application is incomplete'
        data['notification_url'] = 'onboarding_bp.apply_for_membership'

    return render_template('onboarding/account.html', data=data)
