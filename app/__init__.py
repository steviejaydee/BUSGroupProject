from flask import Flask
from flask_mail import Mail
app = Flask(__name__, static_folder='static')
app.secret_key = "secret"

app.config['MAIL_SERVER'] = '127.0.0.1'
app.config['MAIL_PORT'] = 8025
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False

mail =  Mail(app)
from app import routes
