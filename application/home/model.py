import os
import logging
import MySQLdb
from flask import current_app
from datetime import datetime

class User:
    INSERT_SQL = """insert into user(email) \
    values('{}')"""

    def __init__(self, email):
        self.email = email

    def save(self):
        env = os.getenv('SERVER_SOFTWARE')
        if (env and env.startswith('Google App Engine/')):
          # Connecting from App Engine
          db = MySQLdb.connect(
              unix_socket = current_app.config['DB_HOST'],
              user = current_app.config['DB_USERNAME'],
              passwd = current_app.config['DB_PASSWORD'],
              db = current_app.config['DB_NAME'])
        else:
          # Connecting from an external network.
          # Make sure your network is whitelisted
          db = MySQLdb.connect(
            host='localhost',
            port=3306,
            user='root',
            passwd='admin',
            db='zdb')
        try:
            cursor = db.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute(User.INSERT_SQL.format(self.email))
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error('failed to save user: %s, exception %s' % (self.email, e))

        db.close()

def init_app(app):
    pass

def create(email):
    user = User(email)
    user.save()
    return user
