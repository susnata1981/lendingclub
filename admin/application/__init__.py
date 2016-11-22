import logging
from flask import current_app, Flask, redirect, url_for, request, session, g
from flask import current_app
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from shared.util import constants
from flask.ext.login import LoginManager
from shared.db.model import *
from shared.services import stripe_client
import traceback

login_manager = LoginManager()
login_manager.login_view = "account_bp.login"

@login_manager.user_loader
def load_user(id):
    return get_account_by_id(id)

def format_datetime(value, format='%m-%d-%Y'):
    if value is None:
        return constants.NOT_AVAILABLE
    return value.strftime(format)

def format_transaction_status(value):
    if value == Transaction.PENDING:
        return 'PENDING'
    elif value == Transaction.IN_PROGRESS:
        return 'IN PROGRESS'
    elif value == RequestMoney.CANCELED:
        return 'CANCELED'
    elif value == Transaction.FAILED:
        return 'FAILED'
    elif value == Transaction.COMPLETED:
        return 'COMPLETED'
    return 'UNKNOWN'

def format_fi_status(value):
    if value == Fi.UNVERFIED:
        return 'UNVERFIED'
    elif value == Fi.VERIFIED:
        return 'VERIFIED'
    return 'UNKNOWN'

def format_value(value, default = constants.NOT_AVAILABLE):
    if value is None:
        return default
    return value

def format_currency(value):
    try:
        return "${:,.2f}".format(value)
    except ValueError:
        return value;

def format_percentage(value):
    try:
        # return "{}%".format(value)
        return "{:,.2f}%".format(value)
    except ValueError:
        return value;

def format_loan_status(value):
    if value == RequestMoney.IN_REVIEW:
        return 'IN REVIEW'
    elif value == RequestMoney.APPROVED:
        return 'APPROVED'
    elif value == RequestMoney.CANCELED:
        return 'CANCELED'
    elif value == RequestMoney.DECLINED:
        return 'DECLINED'
    elif value == RequestMoney.ACCEPTED:
        return 'ACCEPTED'
    elif value == RequestMoney.TRANSFER_IN_PROGRESS:
        return 'TRANSFER IN PROGRESS'
    elif value == RequestMoney.ACTIVE:
        return 'ACTIVE'
    elif value == RequestMoney.PAID_OFF:
        return 'PAID_OFF'
    elif value == RequestMoney.DELINQUENT:
        return 'DELINQUENT'
    elif value == RequestMoney.IN_COLLECTION:
        return 'IN COLLECTION'
    elif value == RequestMoney.WRITE_OFF:
        return 'WRITE OFF'
    return 'UNKNOWN'

def setup_jinja_filter(app):
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['format_value'] = format_value
    app.jinja_env.filters['format_currency'] = format_currency
    app.jinja_env.filters['format_percentage'] = format_percentage
    app.jinja_env.filters['format_transaction_status'] = format_transaction_status
    app.jinja_env.filters['format_fi_status'] = format_fi_status
    app.jinja_env.filters['format_loan_status'] = format_loan_status

def create_app(config, debug=False, testing=False, config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(config)

    app.debug = debug
    app.testing = testing

    setup_jinja_filter(app)

    if config_overrides:
        app.config.update(config_overrides)

    # Configure logging
    if not app.testing:
        logging.basicConfig(level=logging.INFO)

    login_manager.init_app(app)

    # Setup the data model.
    with app.app_context():
        init_db()
        constants.init()
        stripe_client.init()

    # Account
    from account.controller import account_bp
    app.register_blueprint(account_bp)

    # Add a default root route.
    @app.route("/")
    def index():
        return redirect(url_for('account_bp.dashboard'))

    @app.errorhandler(Exception)
    def log_unhandled_exceptions(error):
        traceback.print_exc()
        logging.error('Faild to serve request with error: %s' % error)

    # @app.before_request
    # def before_request():
    #     print 'before request called for ',request

    # @app.after_request
    # def after_request(response):
    #     print '*********************************  after response called...',response
    #     session['notifications'] = []
    #     return response

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        current_app.db_session.remove()

    # Add an error handler. This is useful for debugging the live application,
    # however, you should disable the output of the exception for production
    # applications.
    @app.errorhandler(500)
    def server_error(e):
        return """
        An internal error occurred: <pre>{}</pre>
        See logs for full stacktrace.
        """.format(e), 500

    return app
