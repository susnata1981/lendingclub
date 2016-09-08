import logging
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
# from gcloud import datastore
from datetime import datetime
# from application import get_model
from .. import onboarding

home_blueprint = Blueprint('home_blueprint', __name__)

# @home_blueprint.route('/')
# def index():
#     return render_template('home/index.html')

@home_blueprint.route('/', methods=['GET'])
def index():
    # model.initialize()
    return render_template('home/index.html',
    disable_production_mode = not current_app.config['ENABLE_PRODUCTION_MODE'])

@home_blueprint.route('/register_user', methods=['POST'])
def register_user():
    if request.method == 'POST':
        email = request.form['email']
        # user = get_model().create(email)
        user = onboarding.model.User(email = email)
        current_app.db_session.add(user)
        current_app.db_session.commit()
        return redirect(url_for('.index'))
    else:
        render_template('404.html')

@home_blueprint.route('/register_user_ajax', methods=['POST'])
def register_user_ajax():
    if request.method == 'POST':
        try:
            email = request.form['email']
            user = onboarding.model.User(email = email)
            current_app.db_session.add(user)
            current_app.db_session.commit()
            logging.info('Saved user %s' % email)
            return jsonify(email=email)
        except Exception as e:
            logging.error('failed to save user, error = %s' % str(e))
            return jsonify(
                error='true',
                description=str(e))
    else:
        return jsonify(
            error='true',
            description='Only support POST request!')

#### TESTING ONLY
@home_blueprint.route('/_add', methods=["POST"])
def add():
    if request.method == 'POST':
        a = int(request.form['a'])
        b = int(request.form['b'])
        print 'a ='+str(a)
        return str(a+b)
    else:
        return str(-1)
