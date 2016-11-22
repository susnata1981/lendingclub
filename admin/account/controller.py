from flask import Blueprint, render_template, session, request, redirect, url_for, jsonify
from flask.ext.login import current_user, login_required, login_user, logout_user
from forms import *
from shared.bli import account as accountBLI
from shared.bli import lending as lendingBLI
from shared.db.model import *

from shared.util import constants, error
import traceback
from pprint import pprint
import json

account_bp = Blueprint('account_bp', __name__, url_prefix='/account')

@account_bp.route('/dashboard', methods=['GET'])
def dashboard():
    data = {}
    data['accounts'] = get_accounts()
    return render_template('account/list.html', data=data)

@account_bp.route('/get_loans', methods=['GET'])
def get_loans():
    account_id = request.args.get('account_id')
    account = get_account_by_id(account_id)
    data = {}
    data['loans'] = []
    for loan in account.request_money_list:
        temp = {}
        temp['loan'] = loan.__dict__
        temp['transactions'] = []
        transactions = lendingBLI.get_loan_schedule_by_id(account_id, loan.id)
        for t in transactions:
            temp['transactions'].append(t)
        data['loans'].append(temp)
    pprint(data)
    return render_template('account/loanrequests.html', data = data)

@account_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        try:
            account = accountBLI.verify_login(form.email.data, form.password.data)
            if account.email == 'susnata@gmail.com':
                login_user(account)
                return redirect(url_for('.dashboard'))
        except Exception as e:
            print 'Exception::',e
            print traceback.format_exc()
            return render_template('404.html')
    return render_template('account/login.html', form=form)

@account_bp.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for('.login'))
