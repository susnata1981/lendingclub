from flask import Blueprint, render_template, session, request, redirect
from flask import current_app
from plaid import Client

login_bp = Blueprint('login_bp', __name__, url_prefix='/login')

@login_bp.route('/', methods=['GET'])
def index():
    return render_template('signup/index.html')

@login_bp.route('/login', methods=['POST'])
def login():
    return redirect('/setup/account')
