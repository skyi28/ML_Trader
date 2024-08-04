from flask import Blueprint, render_template, redirect, flash, request, url_for, send_from_directory
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from website.user import User
from website.app import db
from infrastructure.database import Database


endpoint = Blueprint('endpoints', __name__)

postgres_db = Database()

# TODO Figure out how to use HTML file as blueprint for other ones

@endpoint.route('/favicon.ico')
def favicon():
    return url_for('static', filename='images/favicon.ico')

@endpoint.route('/')
def index():
    return f'Hello World'

@endpoint.route('/training', methods=['GET', 'POST'])
def training():
    if request.method == 'GET':
        return render_template('training.html')
    if request.method == 'POST':
        return f"{request.form.to_dict()}"

@endpoint.route('/dashboard')
def dashboard():
    """
    This function renders the dashboard page with the current user's information and a default symbol.

    Parameters:
    None

    Returns:
    render_template: A Flask function that renders a template with the provided arguments.
        - 'dashboard.html': The name of the template file to render.
        - user: The current user object.
        - symbol: A default symbol to display on the dashboard.
    """
    return render_template('dashboard.html', user=current_user, symbol='BTCUSD')

@endpoint.route('/login', methods=['GET', 'POST'])
def login():
    """
    This function handles user login. It checks the user's email and password against the database,
    and logs the user in if the credentials are correct. If the user is already logged in, they are redirected to their account page.

    Parameters:
    - None

    Returns:
    render_template: A Flask function that renders a template with the provided arguments.
        - 'login.html': The name of the template file to render.
        - user: The current user object. If the user is not logged in, this will be None.

    redirect: A Flask function that redirects the user to a different URL.
        - url_for('endpoint.account'): The URL to redirect the user to after successful login.
    """
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('endpoint.account'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@endpoint.route('/logout')
@login_required
def logout():
    """
    This function handles user logout. It logs the user out of the application and redirects them to the login page.

    Parameters:
    - None

    Returns:
    redirect: A Flask function that redirects the user to a different URL.
        - url_for('endpoint.login'): The URL to redirect the user to after successful logout.
    """
    logout_user()
    return redirect(url_for('endpoint.login'))


@endpoint.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    """
    This function handles user sign-up. It validates user input, checks if the email already exists,
    and creates a new user in the database if the input is valid.

    Parameters:
    - request: A Flask request object containing the user's input.

    Returns:
    render_template: A Flask function that renders a template with the provided arguments.
        - 'sign_up.html': The name of the template file to render.
        - user: The current user object. If the user is not logged in, this will be None.

    redirect: A Flask function that redirects the user to a different URL.
        - url_for('endpoints.index'): The URL to redirect the user to after successful sign-up.
    """
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        
        # TODO Make this checks more meaningful 
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user_id = postgres_db.provide_uniue_user_id()
            new_user = User(id=new_user_id, email=email, first_name=first_name, last_name=last_name, password=generate_password_hash(password1))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('endpoints.index'))

    return render_template("sign_up.html", user=current_user)