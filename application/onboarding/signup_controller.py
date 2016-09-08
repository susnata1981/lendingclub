from flask import Blueprint, render_template, session, request, redirect
from flask import current_app
from plaid import Client

signup_bp = Blueprint('signup_bp', __name__, url_prefix='/signup')

# @signup_bp.route('/', methods=['GET', 'POST'])
# def signup():
#     if request.method == 'GET':
#         return render_template('signup/index.html')
#     elif request.method == 'POST':
#         return redirect('/setup/account')
