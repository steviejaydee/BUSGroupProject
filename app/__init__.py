from flask import Flask
from flask_mail import Mail
from config import Config
import os

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
mail =  Mail(app)
download_folder = os.path.join(app.root_path, "downloads")
app.config['DOWNLOAD_FOLDER'] = download_folder

from app import routes
