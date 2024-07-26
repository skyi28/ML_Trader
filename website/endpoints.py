from flask import Blueprint, render_template, redirect
from flask_login import login_required, current_user

views = Blueprint('endpoints', __name__) # could be that this needs to be renamed to views

@views.route('/')
def index():
    return f'Hello World'