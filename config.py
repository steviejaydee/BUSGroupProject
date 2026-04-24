import os
basedir = os.path.abspath(os.path.dirname(__file__)) # links our database file

class Config:
    SECRET_KEY = "secret"
    MAIL_SERVER = '127.0.0.1'
    MAIL_PORT = 8025
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_STARTTLS = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or None
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or None
    ADMINS = ['admin@uniwell.com']