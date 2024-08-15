"""
Implements an user in the database.
"""
from website.app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    """
    This class represents an user in the database and is needed by flasks login manager to login / logout users.
    The table in the database must be created containing exactly the same columns. 
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
