import os
import logging
from flask import current_app, g
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, Integer, Float, String, DateTime, Text
from sqlalchemy.orm import relationship
from application.util import common
from passlib.hash import sha256_crypt

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=False)
    time_created = Column(DateTime, nullable=False)

    def __repr__(self):
        return "User(id = %d, email = %s)" % (self.id, self.email)

class Account(Base):
    __tablename__ = 'account'

    UNVERIFIED = 0
    VERIFIED_PHONE = 2
    VERIFIED_EMAIL = 4
    VERIFIED = 8

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    ssn = Column(Integer, nullable=True)
    dob = Column(String(24), nullable=True)
    driver_license_number = Column(String(128), nullable=True)
    employer_name = Column(String(255), nullable=True)
    employer_phone_number = Column(String(128), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    phone_number = Column(String(50), unique=True, nullable=False)
    _password = Column(String(1024), nullable=False)
    status = Column(Integer, default=UNVERIFIED, nullable=False)
    phone_verification_code = Column(Integer, nullable=True)
    time_created = Column(DateTime)
    time_updated = Column(DateTime)

    def __repr__(self):
        return "<Account(first_name %s last_name %s phone_number %s password %s)" \
        % (self.first_name, self.last_name, self.phone_number, self._password)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        # self._password = hashpw(password.encode('utf-8'), gensalt())
        self._password = sha256_crypt.encrypt(password)

    def password_match(self, password):
        # return hashpw(password.encode('utf-8'), self._password) == self._password
        return sha256_crypt.verify(password, self._password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return status != UNVERIFIED

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

class Address(Base):
    __tablename__ = 'address'
    INDIVIDUAL, EMPLOYER = range(2)

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id'))
    account = relationship('Account', back_populates='addresses')
    street1 = Column(String(512), nullable=False)
    street2 = Column(String(512), nullable=True)
    city = Column(String(128), nullable=False)
    state = Column(String(128), nullable=False)
    postal_code = Column(Integer, nullable=False)
    address_type = Column(Integer, nullable=False)
    time_created = Column(DateTime)
    time_updated = Column(DateTime)

    def format_single_line():
        return "{0} {1} {2} {3} {4}".format(
        self.street1, self.street2, self.city, self.state, self.postal_code)

class Fi(Base):
    __tablename__ = 'fi'

    INSTANT, RANDOM_DEPOSIT = range(2)
    UNVERFIED, VERIFIED = range(2)

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id'))
    account = relationship('Account', back_populates='fis')
    bank_account_id = Column(String(255), nullable=False)
    verification_type = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False)
    subtype = Column(String(128), nullable=True)
    subtype_name = Column(String(255), nullable=True)
    account_name = Column(String(255), nullable=True)
    institution = Column(String(255), nullable=True)
    institution_type = Column(String(255), nullable=True)
    available_balance = Column(Float, nullable=True)
    current_balance = Column(Float, nullable=True)
    account_type = Column(String(128), nullable=True)
    access_token = Column(String(255), nullable=False, unique=True)
    stripe_bank_account_token = Column(String(255), nullable=True, unique=True)
    account_number_last_4 = Column(Integer, nullable=True)
    time_created = Column(DateTime)
    time_updated = Column(DateTime)


class Plan(Base):
    __tablename__ = "plan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    max_loan_amount = Column(Integer, nullable=False)
    loan_frequency = Column(Integer, nullable=False)
    interest_rate = Column(Float, nullable=False)
    interest_rate_description = Column(Text, nullable=False)
    cost = Column(Float, nullable=False)
    rewards_description = Column(Text, nullable=False)

class Membership(Base):
    __tablename__ = 'membership'

    PENDING, APPROVED, REJECTED = range(3)
    STATUS_NAME = {
        PENDING: "PENDING",
        APPROVED: "APPROVED",
        REJECTED: "REJECTED"
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id'))
    account = relationship('Account', back_populates='memberships')
    plan_id = Column(Integer, ForeignKey('plan.id'))
    plan = relationship('Plan', uselist=False)
    status = Column(Integer, nullable=False)
    time_created = Column(DateTime)
    time_updated = Column(DateTime)

    def is_active(self):
        return self.status == Membership.APPROVED

    def is_pending(self):
        return self.status == Membership.PENDING

    def is_rejected(self):
        return self.status == Membership.REJECTED

    def get_status(self):
        return Membership.STATUS_NAME.get(self.status)

class MembershipPayment(Base):
    __tablename__ = "membership_payment"

    FAILED, COMPLETED = range(2)

    id = Column(Integer, primary_key=True, autoincrement=True)
    memberhip_id = Column(Integer, ForeignKey('membership.id'))
    membership = relationship('Membership', back_populates='payments')
    status = Column(Integer, nullable=False)
    memo = Column(Text, nullable=True)
    time_updated = Column(DateTime)
    time_created = Column(DateTime)

class IAVInstitutions(Base):
    __tablename__ = "iav_institutions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    plaid_id = Column(String(128), nullable=False)

class RequestMoney(Base):
    __tablename__ = "request_money"

    PENDING, IN_PROGRESS, CANCELED, TRANFERRED, PAYMENT_DUE, PARTIAL_PAYMENT_COMPLETED, PAYMENT_COMPLETED = range(7)

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id'))
    account = relationship('Account', back_populates="request_money_list")
    amount = Column(Float, nullable=False)
    status = Column(Integer, nullable=False)
    payment_date = Column(DateTime, nullable=False)
    memo = Column(Text, nullable=True)
    time_updated = Column(DateTime)
    time_created = Column(DateTime)

class ExtensionRequest(Base):
    __tablename__ = "extensions"

    PENDING, CANCELED, REJECTED, APPROVED = range(4)

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey('request_money.id'))
    request = relationship('RequestMoney', back_populates="extensions")
    status = Column(Integer, nullable=False)
    payment_date = Column(DateTime, nullable=False)
    memo = Column(Text, nullable=True)
    time_updated = Column(DateTime)
    time_created = Column(DateTime)

class Transaction(Base):
    __tablename__ = 'transaction'

    PENDING, IN_PROGRESS, CANCELED, FAILED, COMPLETED = range(5)
    BORROW, PAYMENT, INTEREST_CHARGE = range(3)
    USER_INITIATED, AUTOMATIC, MANUAL = range(3)

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey('request_money.id'))
    transaction_type = Column(Integer, nullable=False)
    stripe_transaction_id = Column(String(255), nullable=True)
    status = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    initiated_by = Column(Integer, nullable=False)
    memo = Column(Text, nullable=True)
    time_created = Column(DateTime)
    time_updated = Column(DateTime)


Account.fis = relationship('Fi', order_by=Fi.id, back_populates='account')
Account.addresses = relationship('Address', back_populates='account')
Account.memberships = relationship('Membership', back_populates='account')
Account.employer_address = relationship('Address', uselist = False, back_populates='account')
Account.request_money_list = relationship('RequestMoney', back_populates='account')
RequestMoney.extensions = relationship('ExtensionRequest', back_populates='request')
Membership.payments = relationship('MembershipPayment', back_populates='membership')

def create_plan():
    current_app.db_session.add(
        Plan(
            name = 'Anytime 150',
            max_loan_amount = 150,
            loan_frequency = 3,
            interest_rate = 15,
            interest_rate_description = '0% APR for 30 days and then $15 per $100 every month',
            cost = 10,
            rewards_description = 'Earn points for paying back in time'))
    current_app.db_session.add(
        Plan(
            name = 'Anytime 300',
            max_loan_amount = 300,
            loan_frequency = 3,
            interest_rate = 15,
            interest_rate_description = '0% APR for 30 days and then $15 per $100 every month',
            cost = 18,
            rewards_description = 'Earn points for paying back in time'))
    current_app.db_session.add(
        Plan(
            name = 'Anytime 500',
            max_loan_amount = 500,
            loan_frequency = 3,
            interest_rate = 15,
            interest_rate_description = '0% APR for 30 days and then $15 per $100 every month',
            cost = 35,
            rewards_description = 'Earn points for paying back in time'))
    current_app.db_session.commit()


def recreate_tables(engine):
    logging.info('******* recreating tables ********')
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logging.info('******* done recreating tables ********')
    create_plan()
    logging.info('creating lending plans')

def init_db():
    env = os.getenv('SERVER_SOFTWARE')
    if common.is_running_on_app_engine():
        engine = create_engine(current_app.config['SQLALCHEMY_DB_URL_APP_ENGINE'], echo=True)
    else:
        engine = create_engine(current_app.config['SQLALCHEMY_DB_URL_LOCAL'], echo=True)
    current_app.db_session = db_session = scoped_session(sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine))
    # recreate_tables(engine)

def get_account_by_id(account_id):
    return current_app.db_session.query(Account).filter(Account.id == account_id).one_or_none()


def get_account_by_phone_number(phone_number):
    return current_app.db_session.query(Account).filter(Account.phone_number == phone_number).one_or_none()

def get_all_plans():
    return current_app.db_session.query(Plan).all()

def get_plan_by_id(plan_id):
    return current_app.db_session.query(Plan).filter(Plan.id == plan_id).one()

def get_fi_by_access_token(bank_account_id):
    return current_app.db_session.query(Fi).filter(Fi.bank_account_id == bank_account_id).one_or_none()

def get_fi_by_stripe_bank_account_token(stripe_bank_account_token):
    return current_app.db_session.query(Fi).filter(
    Fi.stripe_bank_account_token == stripe_bank_account_token).one_or_none()

def clear_institutions_table():
    current_app.db_session.query(IAVInstitutions).delete()

def get_all_iav_supported_institutions():
    return current_app.db_session.query(IAVInstitutions).all()
