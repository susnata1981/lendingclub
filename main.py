# """`main` is the top level module for your Flask application."""
#
# # Import the Flask Framework
# from flask import Flask
# app = Flask(__name__)
# # Note: We don't need to call run() since our application is embedded within
# # the App Engine WSGI application server.
#
#
# @app.route('/')
# def hello():
#     """Return a friendly HTTP greeting."""
#     return 'Hello World!'
#
#
# @app.errorhandler(404)
# def page_not_found(e):
#     """Return a custom 404 error."""
#     return 'Sorry, Nothing at this URL.', 404
#
#
# @app.errorhandler(500)
# def application_error(e):
#     """Return a custom 500 error."""
#     return 'Sorry, unexpected error: {}'.format(e), 500

import application
import config

app = application.create_app(config)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)


# from test.a import samplea
#
# if __name__ == "__main__":
#     # b.init()
#     samplea.hello()
