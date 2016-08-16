# from gcloud import datastore
# from flask import current_app
# from datetime import datetime
#
# def get_client():
#     # print 'project id',current_app.config['PROJECT_ID']
#     return datastore.Client('bookshelf-1384')#current_app.config['PROJECT_ID'])
#
# def from_datastore(entity):
#     if not entity:
#         return None
#     entity['id'] = entity.key.id
#     return entity
#
# def save_user(email):
#     ds = get_client()
#     key = ds.key('User')
#     entity = datastore.Entity(key=key)
#     entity['email'] = email
#     entity['time_created'] = datetime.now()
#     e = ds.put(entity)
#     print 'USER ='+str(e)
#     return from_datastore(entity)
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

def init_app(app):
    db.init_app(app)

def from_sql(row):
    """Translates a SQLAlchemy model instance into a dictionary"""
    data = row.__dict__.copy()
    data['id'] = row.id
    data.pop('_sa_instance_state')
    return data

# Start model
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    time_created = db.Column(db.Date)

    def __init__(self, email):
        self.email = email
        self.time_created = datetime.now()

    def __repr__():
        return "<User(email=%s)" % self.email
# End model

def create(email):
    user = User(email=email)
    db.session.add(user)
    db.session.commit()
    return from_sql(user)

def list():
    return User.query.order_by(User.time_created).all()
