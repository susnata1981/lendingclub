### DO NOT USE ###

import os
import logging
import MySQLdb
from flask import current_app
from datetime import datetime
from sqlalchemy.engine import create_engine

CREATE_ACCOUNT_TABLE = """
    create table account(id int not null primary key auto_increment,
        first_name varchar(255) not null,
        last_name varchar(255) not null,
        email varchar(255) not null,
        phone varchar(255) not null,
        time_updated timestamp not null on update now(),
        time_created timestamp not null default CURRENT_TIMESTAMP)"""

def init_app(app):
    pass

def get_db():
    env = os.getenv('SERVER_SOFTWARE')
    print 'ENVIRONMENT  = %s' % env
    if (env and env.startswith('Google App Engine/')):
      # Connecting from App Engine
      return MySQLdb.connect(
          unix_socket = current_app.config['DB_HOST'],
          user = current_app.config['DB_USERNAME'],
          passwd = current_app.config['DB_PASSWORD'],
          db = current_app.config['DB_NAME'])
    else:
      # Connecting from an external network.
      # Make sure your network is whitelisted
      return MySQLdb.connect(
        host='localhost',
        port=3306,
        user='root',
        passwd='admin',
        db='zdb')

def initialize():
    logging.info('connecting to %s' % current_app.config['SQLALCHEMY_DB_URL'])
    engine = create_engine(current_app.config['SQLALCHEMY_DB_URL'])
    conn = engine.connect()
    logging.info('connection successful')
    result = conn.execute("SELECT email from Account")
    for row in result:
        logging.info('Email : %s' % row)
    conn.close()
    logging.info('connection closed')

class User:
    INSERT_SQL = """insert into user(email) \
    values('{}')"""

    def __init__(self, email):
        self.email = email

    def save(self):
        try:
            db = get_db()
            cursor = db.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute(User.INSERT_SQL.format(self.email))
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error('failed to save user: %s, exception %s' % (self.email, e))

        db.close()

class Account:
    INSERT_SQL = """insert into account(first_name, last_name, email, phone)
    values('{0},{1},{2},{3}')"""

    FIND_ACCOUNT_BY_EMAIL = """select first_name, last_name, email, phone from account
     where email = '{}'"""

    def __init__(self, first_name, last_name, email, phone):
        self.id = 0
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.time_created = ''
        self.time_updated = ''

    def save(self):
        try:
            db = get_db()
            cursor = db.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute(Account.INSERT_SQL.format(
                self.first_name, self.last_name, self.email, self.phone))
            db.commit()
            self.id = cursor.lastrowid
            return self
        except Exception as e:
            db.rollback()
            logging.error('failed to create account for user %s' % self)

    def get_account_by_email(self, email):
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(Account.FIND_ACCOUNT_BY_EMAIL.format(email))
            return cursor.fetchone()
        except Exception as e:
            db.rollback()
            logging.error('failed to get account with email %s, exception %s' % (email, e))

    def __repr__(self):
        return "name : %s, %s email : %s phone : %s" % (self.first_name, self.last_name, self.email, self.phone)

class FinancialInstrument:
    INSERT_SQL = """insert into account(first_name, last_name, email, phone)
    values('{0},{1},{2},{3}')"""

    def __init__(self, account_id, access_token):
        self.id = 0
        self.account_id = account_id
        self.access_token = access_token

    def save(self):
        try:
            db = get_db()
            cursor = db.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute(Account.INSERT_SQL.format(
                self.first_name, self.last_name, self.email, self.phone))
            db.commit()
            self.id = cursor.lastrowid
            return self
        except Exception as e:
            db.rollback()
            logging.error('failed to create account for user %s' % self)

def create(email):
    user = User(email)
    user.save()
    return user
