import os
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
from config.config import load_config


config = load_config(f'{path_to_config}{os.sep}config.yaml')
db = SQLAlchemy()

def create_app():
    """
    This function creates and configures a Flask application with SQLAlchemy and Flask-Login.

    Returns:
    - app: A configured Flask application instance.
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{config.postgres.username}:{config.postgres.password}@{config.postgres.host}:{config.postgres.port}/{config.postgres.database}'
    db.init_app(app)

    from website.endpoints import endpoint

    app.register_blueprint(endpoint, url_prefix='/')

    from website.user import User

    login_manager = LoginManager()
    login_manager.login_view = 'endpoint.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        """
        This function loads a user by their ID.

        Parameters:
        - id (int): The ID of the user to load.

        Returns:
        - User: The loaded user object.
        """
        return User.query.get(int(id))

    return app
