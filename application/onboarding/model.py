import os
from flask import current_app, g
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Column, Integer, Float, String, DateTime, Text
from sqlalchemy.orm import relationship
# from bcrypt import hashpw, gensalt
from passlib.hash import sha256_crypt

Base = declarative_base()

def init_db():
    env = os.getenv('SERVER_SOFTWARE')
    print 'ENVIRONMENT  = %s' % env
    if (env and env.startswith('Google App Engine/')):
        engine = create_engine(current_app.config['SQLALCHEMY_DB_URL_APP_ENGINE'], echo=True)
    else:
        engine = create_engine(current_app.config['SQLALCHEMY_DB_URL_LOCAL'], echo=True)
    current_app.db_session = db_session = scoped_session(sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine))
    # Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255))

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

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id'))
    account = relationship('Account', back_populates='address')
    street1 = Column(String(512), nullable=False)
    street2 = Column(String(512), nullable=True)
    city = Column(String(128), nullable=False)
    state = Column(String(128), nullable=False)
    postal_code = Column(Integer, nullable=False)
    time_created = Column(DateTime)
    time_updated = Column(DateTime)

class Fi(Base):
    __tablename__ = 'fi'

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id'))
    account = relationship('Account', back_populates='fis')
    bank_account_id = Column(String(512), nullable=False)
    subtype = Column(String(128), nullable=True)
    subtype_name = Column(String(256), nullable=True)
    account_name = Column(String(256), nullable=True)
    institution = Column(String(256), nullable=True)
    institution_type = Column(String(256), nullable=True)
    available_balance = Column(Float, nullable=True)
    current_balance = Column(Float, nullable=True)
    account_type = Column(String(128), nullable=True)
    access_token = Column(String(512), nullable=False)
    stripe_bank_account_token = Column(String(512), nullable=True)
    account_number_last_4 = Column(Integer, nullable=True)
    time_created = Column(DateTime)
    time_updated = Column(DateTime)

class Transaction(Base):
    __tablename__ = 'transaction'
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey('account.id'))
    account = relationship('Account', back_populates='transaction')
    data = Column(Text, nullable=False)
    time_created = Column(DateTime)
    time_updated = Column(DateTime)

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
    status = Column(Integer, nullable=False)
    time_created = Column(DateTime)
    time_updated = Column(DateTime)

    def is_active(self):
        return self.status == Membership.APPROVED

    def is_rejected(self):
        return self.status == Membership.REJECTED

    def get_status(self):
        return Membership.STATUS_NAME.get(self.status)

Account.fis = relationship('Fi', order_by=Fi.id, back_populates='account')
Account.transaction = relationship('Transaction', back_populates='account')
Account.address = relationship('Address', uselist = False, back_populates='account')
Account.memberships = relationship('Membership', back_populates='account')

def get_account_by_id(account_id):
    return current_app.db_session.query(Account).filter(Account.id == account_id).one_or_none()

def get_account_by_phone_number(phone_number):
    return current_app.db_session.query(Account).filter(Account.phone_number == phone_number).one_or_none()
