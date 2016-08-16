from flask import Blueprint, render_template, request, redirect, url_for
from gcloud import datastore
from datetime import datetime
from application import get_model

home_blueprint = Blueprint('home', __name__)

@home_blueprint.route('/')
def index():
    return render_template('home/index.html')

@home_blueprint.route('/register_user', methods=['POST'])
def register_user():
    if request.method == 'POST':
        email = request.form['email']
        user = get_model().create(email)
        return redirect(url_for('.index'))
    else:
        render_template('404.html')

@home_blueprint.route('/_add', methods=["POST"])
def add():
    if request.method == 'POST':
        a = int(request.form['a'])
        b = int(request.form['b'])
        print 'a ='+str(a)
        return str(a+b)
    else:
        return str(-1)
