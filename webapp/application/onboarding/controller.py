from flask import Blueprint, render_template, session, request, redirect, url_for, jsonify
from shared.services import stripe_client
from forms import *
from shared.db.model import *
import traceback
import random
from datetime import datetime
from flask.ext.login import current_user, login_required, login_user, logout_user
from shared.util import constants, error, util
from shared import services
from shared.bli import account as accountBLI
from pprint import pprint
import json
import logging
import dateutil
from dateutil.relativedelta import relativedelta
from shared.bli import bank as bankBLI
from shared.bli.viewmodel.bank_data import *
from shared.bli.viewmodel.onboarding_step_vm import *

### FOR DEMO ONLY
from flask.ext.login import login_user
import random, string
### END DEMO ONLY #####

onboarding_bp = Blueprint('onboarding_bp', __name__, url_prefix='/onboarding')

@onboarding_bp.route('/verify/resend', methods=['GET', 'POST'])
def resend_email_verification():
    form = ResendEmailVerificationForm(request.form)
    data = {}
    if form.validate_on_submit():
        email = form.email.data
        try:
            account = get_account_by_email(email)
            if not account:
                util.flash_error('Account for this email(%s) doesn\'t exist at Ziplly.' % (email))
                data['show_email_verification_form'] = True
            elif accountBLI.is_email_verified(account):
                util.flash_error('Email already verified.')
                data['email_already_verified'] = True
            else:
                try:
                    accountBLI.initiate_email_verification(account)
                    data['email_sent'] = True
                except error.EmailVerificationSendingError:
                    util.flash_error(constants.EMAIL_VERIFICATION_SEND_FAILURE_MESSAGE)
                    data['show_email_verification_form'] = True
        except Exception:
            util.flash_error(constants.GENERIC_ERROR)
            data['show_email_verification_form'] = True
    else:
        data['show_email_verification_form'] = True
    return render_template('onboarding/verify_email.html', data=data, form=form)

@onboarding_bp.route('/<id>/verify', methods=['GET'])
def verify_email(id):
    form = ResendEmailVerificationForm(request.form)
    token = request.args.get(constants.VERIFICATION_TOKEN_NAME)
    data = {}
    try:
        accountBLI.verify_email(int(id), token)
        return redirect(url_for('onboarding_bp.account_verified'))
    except (error.AccountNotFoundError, error.EmailVerificationNotMatchError) as e:
        util.flash_error('Invalid verification code.')
        data['show_email_verification_form'] = True
    except error.AccountEmailAlreadyVerifiedError:
        util.flash_error('Email already verified.')
        data['email_already_verified'] = True
    except error.DatabaseError:
        util.flash_error(constants.GENERIC_ERROR)
        data['show_email_verification_form'] = True
    return render_template('onboarding/verify_email.html', data=data, form=form)

@onboarding_bp.route('/account_verified', methods=['GET'])
def account_verified():
    return render_template('onboarding/account_verified.html')

@onboarding_bp.route('/', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('account_bp.account'))

    form = SignupForm(request.form)
    print 'errors - ',form.errors
    if request.method == 'GET':
        ### FOR DEMO ONLY #####
        form.first_name.data = 'Jane'
        form.last_name.data = 'Doe'
        form.phone_number.data = '408-345-3248'
        t1 = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
        form.email.data = 'demo_'+t1+'@ziplly.com'
        form.dob.data = datetime.strptime('01/01/1970', "%m/%d/%Y")
        form.ssn.data = '453-56-4321'
        #form.password.data = '123456789'
        form.consent.data = True
        form.street1.data = '1122 Demo way'
        form.city.data = 'San Jose'
        form.state.data = 'CA'
        form.postal_code.data = '95101'
        ### END DEMO ONLY #####
    elif form.validate_on_submit():
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
                address_type = Address.INDIVIDUAL,
                time_created = now,
                time_updated = now)

            account.addresses.append(address)

            accountBLI.signup(account)
        except error.AccountExistsError:
            util.flash_error(constants.ACCOUNT_WITH_EMAIL_ALREADT_EXISTS)
            return render_template('onboarding/signup.html', form=form)
        except error.EmailVerificationSendingError:
            util.flash_error(constants.ACCOUNT_CREATED_BUT_EMAIL_VERIFICATION_SEND_FAILURE_MESSAGE)
            data = {}
            data['show_email_verification_form'] = True
            email_form = ResendEmailVerificationForm(request.form)
            return render_template('onboarding/verify_email.html', data=data, form=email_form)
        except error.DatabaseError as de:
            print 'ERROR: Database Exception: %s' % (de.message)
            util.flash_error(constants.GENERIC_ERROR)
            return render_template('onboarding/signup.html', form=form)
        except Exception as e:
            print 'ERROR: General Exception: %s' % (e.message)
            util.flash_error(constants.GENERIC_ERROR)
            return render_template('onboarding/signup.html', form=form)

        # # verify email sent message
        # data = {}
        # data['email_sent'] = True
        # email_form = ResendEmailVerificationForm(request.form)
        # return render_template('onboarding/verify_email.html', data=data, form=email_form)

        #### FOR DEMO ONLY
        #verify the account
        try:
            accountBLI.verify_email(account.id + constants.EMAIL_ACCOUNT_ID_CONSTANT, account.email_verification_token)
        except error.DatabaseError as e:
            print 'ERROR: General Exception: %s' % (e.message)
            util.flash_error(constants.GENERIC_ERROR)
            return render_template('onboarding/signup.html', form=form)
        except Exception as e:
            print 'ERROR: General Exception: %s' % (e.message)
            util.flash_error(constants.GENERIC_ERROR)
            return render_template('onboarding/signup.html', form=form)
        #login account
        login_user(account)
        return redirect(url_for('lending_bp.dashboard'))
        ### END DEMO ONLY #####

    return render_template('onboarding/signup.html', form=form)

@onboarding_bp.route('/add_bank', methods=['GET', 'POST'])
@login_required
def add_bank():
    if request.method == 'GET':
        data = {}
        onboardingStepVM = OnboardingStepVM()
        onboardingStepVM.set_onboarding_state(OnboardingStepVM.LINK_BANK_ACCOUNT, True)
        data['onboarding_steps'] = onboardingStepVM.get_onboarding_steps()
        data['institutions'] = get_all_iav_supported_institutions()
        return render_template('onboarding/add_bank.html', data=data)
    else:
        result = {}
        try:
            # save bank information
            fi = Fi(
                account_name = request.form['bank_account_name'],
                plaid_account_id = request.form['bank_account_id'],
                institution = request.form['institution'],
                institution_type = request.form['institution_type'],
                verification_type = Fi.INSTANT,
                status = Fi.VERIFIED,
                primary = accountBLI.need_primary_bank(current_user),
                usage_status = Fi.ACTIVE,
                time_updated = datetime.now(),
                time_created = datetime.now())
            bankBLI.save_instant_verified_bank(fi, request.form['public_token'], current_user)

            response = {}
            response['success'] = True
            return jsonify(response)
        except error.BankAlreadyAdded as e:
            #TODO: this acocunt id could be present for same user or for different user
            # need to think about what messaging shoud be here.
            result['error'] = True
            result['message'] = constants.BANK_ALREADY_ADDED
            return jsonify(result)
        except Exception as e:
            traceback.print_exc()
            logging.error('add_bank::received exception %s' % e)
            response = {}
            response['error'] = 'true'
            return jsonify(response)

@onboarding_bp.route('/add_random_deposit', methods=['GET', 'POST'])
@login_required
def add_random_deposit():
    form = AddRandomDepositForm(request.form)
    data = {}
    onboardingStepVM = OnboardingStepVM()
    onboardingStepVM.set_onboarding_state(OnboardingStepVM.LINK_BANK_ACCOUNT, True)
    data['onboarding_steps'] = onboardingStepVM.get_onboarding_steps()
    data['institutions'] = get_all_iav_supported_institutions()
    if request.method == 'GET':
        ### FOR DEMO ONLY #####
        form.name.data = current_user.first_name + ' ' + current_user.last_name
        return render_template('onboarding/add_random_deposit.html', form = form, data = data)
        ### END DEMO ONLY #####
    elif form.validate_on_submit():
        try:
            bank = BankData(
                account_number = form.account_number.data,
                routing_number = form.routing_number.data,
                currency = form.currency.data,
                country = form.country.data,
                holder_name = form.name.data,
                verification_type = Fi.RANDOM_DEPOSIT,
                status = Fi.UNVERFIED,
                usage_status = Fi.ACTIVE,
                primary = accountBLI.need_primary_bank(current_user),
            )
            bankBLI.save_random_deposit_bank(bank, current_user)
            return redirect(url_for('.add_bank_random_deposit_success'))
        except error.UserInputError as e:
            util.flash_error(e.message)
            return render_template('onboarding/add_random_deposit.html', form = form)
        except error.StripeError as e:
            util.flash_error(e.message)
            return render_template('onboarding/add_random_deposit.html', form = form)
        except Exception as e:
            #TODO: should we handle if bank already exists for customer?
            logging.error('add_random_deposit::received exception %s' % e)
            util.flash_error(constants.GENERIC_ERROR)
            return render_template('onboarding/add_random_deposit.html', form = form)
    else:
        return render_template('onboarding/add_random_deposit.html', form = form, data = data)

@onboarding_bp.route('/start_random_deposit_verification', methods=['POST'])
@login_required
def start_random_deposit_verification():
    fi_id = request.form.get('fi_id')
    if fi_id:
        session[accountBLI.RANDOM_DEPOSIT_FI_ID_KEY] = fi_id
        return redirect(url_for('.verify_random_deposit'))
    util.flash_error(constants.GENERIC_ERROR)
    return redirect(url_for('lending_bp.dashboard'))

@onboarding_bp.route('/verify_random_deposit', methods=['GET', 'POST'])
@login_required
def verify_random_deposit():
    if not accountBLI.RANDOM_DEPOSIT_FI_ID_KEY in session:
        logging.error('verify_random_deposit call doesn\'t contain %s in session. redirecting to dashboard.' % (accountBLI.RANDOM_DEPOSIT_FI_ID_KEY))
        return redirect(url_for('lending_bp.dashboard'))

    form = VerifyRandomDepositForm(request.form)
    if form.validate_on_submit():
        try:
            bank_deposit = BankDepositData(
                id = session[accountBLI.RANDOM_DEPOSIT_FI_ID_KEY],
                deposit1 = form.deposit1.data,
                deposit2 = form.deposit2.data
            )
            bankBLI.verify_random_deposit(bank_deposit, current_user)

            session.pop(accountBLI.RANDOM_DEPOSIT_FI_ID_KEY, None)
            #TODO: show success and show loan review page if needed
            #return redirect(url_for('.application_complete'))
            return redirect(url_for('lending_bp.dashboard'))
        except error.IncorrectRandomDepositAmountsError as e:
            logging.info('Stripe service raised IncorrectRandomDepositAmountsError')
            util.flash_error(e.message)
            return render_template('onboarding/verify_random_deposit.html', form=form)
        except error.UserInputError as e:
            util.flash_error(e.message)
            return render_template('onboarding/verify_random_deposit.html', form=form)
        except Exception as e:
            logging.error('failed to verify_account_random_deposit, exception %s' % e)
            util.flash_error(constants.GENERIC_ERROR)
            return render_template('onboarding/verify_random_deposit.html', form=form)
    else:
        return render_template('onboarding/verify_random_deposit.html', form=form)

@onboarding_bp.route('/verified', methods=['GET'])
@login_required
def verified():
    data = {}
    onboardingStepVM = OnboardingStepVM()
    onboardingStepVM.set_onboarding_state(OnboardingStepVM.APPLY_LOAN, True)
    data['onboarding_steps'] = onboardingStepVM.get_onboarding_steps()
    return render_template('onboarding/onboarding_complete.html', data=data)

@onboarding_bp.route('/add_bank_random_deposit_success', methods=['GET'])
@login_required
def add_bank_random_deposit_success():
    return render_template('onboarding/add_bank_random_deposit_success.html')

@onboarding_bp.route('/complete_signup', methods=['GET','POST'])
@login_required
def complete_signup():
    steps = accountBLI.signup_steps(current_user)
    if not steps.is_complete(OnboardingStepVM.ENTER_EMPLOYER_INFORMATION):
        return redirect(url_for('.enter_employer_information'))
    elif not steps.is_complete(OnboardingStepVM.LINK_BANK_ACCOUNT):
        return redirect(url_for('onboarding_bp.add_bank'))
    elif not steps.is_complete(OnboardingStepVM.VERIFY_BANK_ACCOUNT):
        session[accountBLI.RANDOM_DEPOSIT_FI_ID_KEY] = steps.verify_bank_id
        return redirect(url_for('onboarding_bp.verify_random_deposit'))
    return redirect(url_for('.dashboard'))

@onboarding_bp.route('/steps', methods=['GET','POST'])
@login_required
def steps():
    steps = accountBLI.signup_steps(current_user)
    data = {}
    data['steps'] = steps.get_signup_steps()
    return render_template('lending/_onboarding_state.html', data=data)

@onboarding_bp.route('/enter_employer_information', methods=['GET', 'POST'])
@login_required
def enter_employer_information():
    onboardingStepVM = OnboardingStepVM()
    onboardingStepVM.set_onboarding_state(OnboardingStepVM.ENTER_EMPLOYER_INFORMATION, True)
    data = {}
    data['onboarding_steps'] = onboardingStepVM.get_onboarding_steps()
    form = EmployerInformationForm(request.form)
    if request.method == 'GET':
        ### FOR DEMO ONLY #####
        form.employer_name.data = 'Best Inc'
        form.employer_phone_number.data = '408-111-2222'
        form.street1.data = '1122 Demo Dr'
        form.city.data = 'San Jose'
        form.state.data = 'CA'
        form.postal_code.data = '95102'
        ### END DEMO ONLY #####
    elif form.validate_on_submit():
        try:
            now = datetime.now()
            employer = Employer(
                type = Employer.TYPE_FROM_NAME[form.employment_type.data],
                name = form.employer_name.data,
                phone_number = form.employer_phone_number.data,
                street1 = form.street1.data,
                street2 = form.street2.data,
                city = form.city.data,
                state = form.state.data,
                postal_code = form.postal_code.data,
                status = Employer.ACTIVE,
                time_created = now,
                time_updated = now)
            accountBLI.add_employer(current_user, employer)
            return redirect(url_for('.complete_signup'))
        except error.DatabaseError as de:
            print 'ERROR: Database Exception: %s' % (de.message)
            util.flash_error(constants.GENERIC_ERROR)
            return render_template('onboarding/enter_employer_information.html', form=form)
        except Exception as e:
            print 'ERROR: General Exception: %s' % (e.message)
            util.flash_error(constants.GENERIC_ERROR)
            return render_template('onboarding/enter_employer_information.html', form=form)
    return render_template('onboarding/enter_employer_information.html', form=form, data=data)


######## Phone verification ###########
def generate_and_store_new_verification_code(account):
    # verification_code = random.randint(1000, 9999)
    verification_code = 1111
    account.phone_verification_code = verification_code
    current_app.db_session.add(account)
    current_app.db_session.commit()
    return verification_code

@onboarding_bp.route('/verify', methods=['GET', 'POST'])
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
            return redirect(url_for('onboarding_bp.account_verified'))
        else:
            util.flash_error('Invalid verification code')
    return render_template('onboarding/verify_phone.html', form=form)

# ajax
@onboarding_bp.route('/resend_verification', methods=['POST'])
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
