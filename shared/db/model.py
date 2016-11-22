import os
import logging
from flask import current_app, g
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from passlib.hash import sha256_crypt
from shared.util import constants

try:
    from shared.util import util
except ImportError:
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'util'))
    import util

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
    email = Column(String(255), unique=True, nullable=True)
    ssn = Column(String(24), nullable=True)
    dob = Column(String(24), nullable=True)
    driver_license_number = Column(String(128), nullable=True)
    employer_name = Column(String(255), nullable=True)
    employer_phone_number = Column(String(128), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=False)
    _password = Column(String(1024), nullable=False)
    status = Column(Integer, default=UNVERIFIED, nullable=False)
    phone_verification_code = Column(Integer, nullable=True)
    email_verification_token = Column(String(128), nullable=True)
    password_reset_token = Column(String(128), nullable=True)
    promotion_code = Column(String(255), nullable=True)
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
        return self.status != Account.UNVERIFIED

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def get_usable_fis(self, verification_status=None, descending=True):
        usable_fis = []
        for fi in self.fis:
            if fi.usage_status == Fi.ACTIVE:
                if verification_status == None:
                    usable_fis.append(fi)
                elif verification_status == fi.status:
                    usable_fis.append(fi)
        if usable_fis:
            usable_fis.sort(key=byTime_key, reverse=descending)
        return usable_fis

    def get_active_primary_bank(self):
        for fi in self.fis:
            if fi.primary and fi.usage_status == Fi.ACTIVE:
                return fi
        return None

    def is_active_primary_bank_verified(self):
        fi = self.get_active_primary_bank()
        if fi and fi.status == Fi.VERIFIED:
            return True
        return False

    def get_open_loans(self):
        try:
            open_loans = current_app.db_session.query(RequestMoney).filter(
            RequestMoney.account_id == id, RequestMoney.status.in_([RequestMoney.IN_REVIEW, RequestMoney.APPROVED, RequestMoney.ACCEPTED, RequestMoney.TRANSFER_IN_PROGRESS, RequestMoney.ACTIVE, RequestMoney.DELINQUENT, RequestMoney.IN_COLLECTION])
            ).all()
            return open_loans
        except Exception as e:
            LOGGER.error(e.message)
            raise error.DatabaseError(constants.GENERIC_ERROR,e)

    def get_open_request(self):
        for req in self.request_money_list:
            if req.status != RequestMoney.CANCELED and \
            req.status != RequestMoney.PAYMENT_COMPLETED and \
            req.status != RequestMoney.REJECTED:
                return req
        return None

    def get_active_plan(self):
        for mem in self.memberships:
            if mem.is_active():
                return mem.plan
        return None

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
    ACTIVE, INACTIVE = range(2)

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id'))
    account = relationship('Account', back_populates='fis')
    plaid_account_id = Column(String(255), nullable=True, unique=True)
    stripe_bank_account_token = Column(String(255), nullable=False, unique=True)
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
    plaid_access_token = Column(String(255), nullable=True, unique=True)
    account_number_last_4 = Column(Integer, nullable=True)
    primary = Column(Boolean, nullable=False)
    usage_status = Column(Integer, nullable=False)
    time_created = Column(DateTime)
    time_updated = Column(DateTime)

class Employer(Base):
    __tablename__ = 'employer'
    FULL_TIME, PART_TIME, SELF_EMPLOYED, UNEMPLOYED  = range(4)
    TYPE_NAME = {
        FULL_TIME: 'full-time',
        PART_TIME: 'part-time',
        SELF_EMPLOYED: 'self-employed',
        UNEMPLOYED: 'unemployed'
    }
    TYPE_FROM_NAME = {
        'full-time': FULL_TIME,
        'part-time': PART_TIME,
        'self-employed': SELF_EMPLOYED,
        'unemployed': UNEMPLOYED
    }
    ACTIVE,IN_ACTIVE = range(2)
    STATUS_NAME = {
        ACTIVE: "ACTIVE",
        IN_ACTIVE: "IN_ACTIVE"
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id'))
    account = relationship('Account', back_populates='employers')
    type = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    phone_number = phone_number = Column(String(50), nullable=False)
    street1 = Column(String(512), nullable=False)
    street2 = Column(String(512), nullable=True)
    city = Column(String(128), nullable=False)
    state = Column(String(128), nullable=False)
    postal_code = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False)
    time_created = Column(DateTime)
    time_updated = Column(DateTime)

    def get_status_name(self):
        return EmployerInformation.STATUS_NAME.get(self.status)

    def get_type_name(self):
        return EmployerInformation.TYPE_NAME.get(self.type)

class IAVInstitutions(Base):
    __tablename__ = "iav_institutions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    institution_type = Column(String(255), nullable=False)
    plaid_id = Column(String(128), nullable=False)

class RequestMoney(Base):
    __tablename__ = "request_money"
    IN_REVIEW, APPROVED, CANCELED, DECLINED, ACCEPTED, TRANSFER_IN_PROGRESS, ACTIVE, PAID_OFF, DELINQUENT, IN_COLLECTION, WRITE_OFF = range(11)

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id'))
    account = relationship('Account', back_populates="request_money_list")
    amount = Column(Float, nullable=False)
    #duration in months
    duration = Column(Integer, nullable=False)
    apr = Column(Float, nullable=True)
    status = Column(Integer, nullable=False)
    fi_id = Column(Integer, ForeignKey('fi.id'))
    fi = relationship('Fi', back_populates="request_money_list")
    memo = Column(Text, nullable=True)
    time_updated = Column(DateTime)
    time_created = Column(DateTime)

class RequestMoneyHistory(Base):
    __tablename__ = "request_money_history"

    id = Column(Integer, ForeignKey('request_money.id'))
    request = relationship('RequestMoney', uselist=False, back_populates="history")
    amount = Column(Float, nullable=False)
    status = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    fi_id = Column(Integer, ForeignKey('account.id'))
    memo = Column(Text, nullable=True)
    time_created = Column(DateTime)
    __table_args__ = (
        PrimaryKeyConstraint('id', 'time_created'),
        {},
    )

class Transaction(Base):
    __tablename__ = 'transaction'

    #status
    PENDING, IN_PROGRESS, CANCELED, FAILED, COMPLETED = range(5)
    #transaction_type
    FULL, PARTIAL = range(2)
    #initiated_by
    USER, AUTOMATIC, MANUAL = range(3)

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey('request_money.id'))
    request = relationship('RequestMoney', back_populates="transactions")
    transaction_type = Column(Integer, nullable=False)
    stripe_transaction_id = Column(String(256), nullable=True)
    status = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(DateTime, nullable=False)
    initiated_by = Column(Integer)
    memo = Column(Text, nullable=True)
    time_created = Column(DateTime)
    time_updated = Column(DateTime)

class TransactionHistory(Base):
    __tablename__ = 'transaction_history'

    id = Column(Integer, ForeignKey('transaction.id'))
    transaction = relationship('Transaction', uselist=False, back_populates="history")
    status = Column(Integer, nullable=False)
    memo = Column(Text, nullable=True)
    time_created = Column(DateTime)
    __table_args__ = (
        PrimaryKeyConstraint('id', 'time_created'),
        {},
    )

Account.fis = relationship('Fi', order_by=Fi.id, back_populates='account')
Account.addresses = relationship('Address', back_populates='account')
Account.employers = relationship('Employer', back_populates='account')
Account.request_money_list = relationship('RequestMoney', back_populates='account', order_by='desc(RequestMoney.id)')
Fi.request_money_list = relationship('RequestMoney', back_populates='fi', order_by='desc(RequestMoney.id)')
RequestMoney.transactions = relationship('Transaction', back_populates='request', order_by='desc(Transaction.id)')
RequestMoney.history = relationship('RequestMoneyHistory', back_populates='request', order_by='desc(RequestMoneyHistory.time_created)')
Transaction.history = relationship('TransactionHistory', back_populates='transaction', order_by='desc(TransactionHistory.time_created)')

def recreate_tables(engine):
    logging.info('******* recreating tables ********')
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logging.info('******* done recreating tables ********')

def init_db():
    if util.is_running_on_app_engine():
        engine = create_engine(current_app.config['SQLALCHEMY_DB_URL_APP_ENGINE'], echo=False)
    else:
        engine = create_engine(current_app.config['SQLALCHEMY_DB_URL_LOCAL'], echo=False)
    current_app.db_session = db_session = scoped_session(sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine))
    # recreate_tables(engine)

def byTime_key(obj):
    return obj.time_updated

def get_account_by_id(account_id):
    return current_app.db_session.query(Account).filter(Account.id == account_id).one_or_none()

def get_accounts():
    return current_app.db_session.query(Account).all()

def get_account_by_phone_number(phone_number):
    return current_app.db_session.query(Account).filter(Account.phone_number == phone_number).one_or_none()

def get_account_by_email(email):
    return current_app.db_session.query(Account).filter(Account.email == email).one_or_none()

def get_fi_by_id(id):
    return current_app.db_session.query(Fi).filter(Fi.id == id).one_or_none()

def get_fi_by_stripe_bank_account_token(stripe_bank_account_token):
    return current_app.db_session.query(Fi).filter(
    Fi.stripe_bank_account_token == stripe_bank_account_token).one_or_none()

def clear_institutions_table():
    current_app.db_session.query(IAVInstitutions).delete()

def get_all_iav_supported_institutions():
    return current_app.db_session.query(IAVInstitutions).all()
