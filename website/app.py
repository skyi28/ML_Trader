"""
This python module contains functions to start a web application.
"""
import os
import sys
basedir = os.path.abspath(os.path.dirname(__file__)) + os.sep
basedir_split = basedir.split(os.sep)
path_to_config = ''
for part in basedir_split:
    path_to_config += part + os.sep
    if part == "ML_Trader":
        path_to_config += f'\config'
        break

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from infrastructure.database import Database
from config.config import load_config
from infrastructure.logger import create_logger

class Application:
    def __init__(self) -> None:
        self.config = load_config(f'{path_to_config}{os.sep}config.yaml')
        
        self.app = Flask(__name__, static_folder='/files/static')
        from website.endpoints import views
        self.app.register_blueprint(views, url_prefix='/')
        
    def run(self):
        # TODO Create self-signed certificate
        self.app.run(host=self.config.webserver.host, 
                     debug=self.config.webserver.debug_mode, 
                     port=self.config.webserver.port, 
                     ssl_context='adhoc')

