"""
This file contains all endpoints which return visible output. All routes which return data to the 
user are defined in api.py. 
"""
from flask import Blueprint, render_template, redirect, flash, request, url_for, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import json
import threading
import datetime
import pandas as pd

from website.user import User
from website.app import db
from infrastructure.database import Database
from models.xgboost_model import XGBoostModel

endpoint = Blueprint('endpoints', __name__)

postgres_db = Database()

# TODO Include a check if the user who send the request is allowed to execute the method for the requested bot
# TODO This whole file needs error handling

@endpoint.route('/favicon.ico')
def favicon():
    """
    This function returns the URL for the favicon.ico file located in the static/images directory.

    Parameters:
    - None

    Returns:
    - str: The URL for the favicon.ico file. This URL can be used in HTML to display the favicon.
    """
    return url_for('static', filename='images/favicon.ico')


@endpoint.route('/start_stop_bot/<int:user>/<int:bot_id>/<string:action>')
def start_stop_bot(user: int, bot_id: int, action: str) -> dict:
    """
    This function updates the 'running' status of a specific bot in the database based on the provided action.

    Parameters:
    - user (int): The ID of the user who owns the bot.
    - bot_id (int): The ID of the bot to be updated.
    - action (str): The action to be performed. It should be either 'True' or 'False' as a string.

    Returns:
    - dict: A JSON response indicating the success of the operation. The response contains a 'success' key with a boolean value.
    """
    postgres_db.update_table(
        table_name='bots',
        column='running',
        value=eval(action),
        where_condition=f'WHERE "user"={user} AND "id"={bot_id}'
    )
    # TODO Check if bot has an open position, if yes close it
    return jsonify(success=True)
@login_required
@endpoint.route('/train/<int:bot_id>', methods=['GET', 'POST'])
def bot_train(bot_id: int):
    """
    This function handles the training process for a specific bot. It retrieves the bot's details from the database,
    and renders a template for training parameters or executes the training process based on user input.

    Parameters:
    - bot_id (int): The unique identifier of the bot to be trained.

    Returns:
    - render_template: If the request method is 'GET', this function renders the 'bot_train.html' template with the bot's details and technical indicators.
    - redirect: If the request method is 'POST', this function redirects the user to the bot's detail page after starting the training process in a separate thread.
    """
    bot = postgres_db.get_bot_by_id(bot_id)
    if request.method == 'GET':
        indicators = bot[8].split(',')
        return render_template('bot_train.html', user=current_user, bot=bot, indicators=indicators)
    elif request.method == 'POST':
        params: dict = request.form.to_dict()
        start_time: datetime.datetime = datetime.datetime.strptime(params['startTime'], '%Y-%m-%dT%H:%M')
        end_time: datetime.datetime = datetime.datetime.strptime(params['endTime'], '%Y-%m-%dT%H:%M')
        if 'useAllData' in params.keys():
            data_percentage = 1
        else:
            data_percentage = float(params['dataPercentage']) / 100

        # TODO get model specific data such us batch size and epochs from the request
        bot_train_thread_args = (
            current_user.get_id(),
            bot,
            start_time,
            end_time,
            data_percentage
        )
        bot_train_thread = threading.Thread(target=bot_train_execute, args=bot_train_thread_args)    
        bot_train_thread.start()

        return redirect(f'/bot/{bot[0]}')


def bot_train_execute(user: int, bot: list, start_time: datetime.datetime, end_time: datetime.datetime, data_percentage: float) -> None:
    """
    This function is responsible for executing the training process for a specific bot and is called by a separate thread.
    It checks the bot's model type and performs the necessary actions based on the model.

    Parameters:
    - user (int): The ID of the user who owns the bot.
    - bot (list): A list containing information about the bot, including its ID, model type, etc.
    - start_time (datetime.datetime): The start time for training data.
    - end_time (datetime.datetime): The end time for training data.
    - data_percentage (float): The percentage of data to be used for training.

    Returns:
    - None: This function does not return any value.
    """
    postgres_db.update_table(
        table_name='bots',
        column='training',
        value=True,
        where_condition=f'WHERE "user"={user} AND "id"={bot[0]}'
    )

    postgres_db.update_table(
        table_name='bots',
        column='training_set_percentage',
        value=data_percentage,
        where_condition=f'WHERE "user"={user} AND "id"={bot[0]}'
    )

    if bot[7].lower() == 'xgboost':
        xgbmodel = XGBoostModel()
        # TODO get hyper parameters from database
        model = xgbmodel.create_model()
        model = xgbmodel.train(
            user=user,
            model_id=bot[0],
            model=model,
            start_date=start_time,
            end_date=end_time,
            train_size=data_percentage
            )

    # Add other model types here

    postgres_db.update_table(
        table_name='bots',
        column='last_trained',
        value=datetime.datetime.now(),
        where_condition=f'WHERE "user"={user} AND "id"={bot[0]}'
    )

    postgres_db.update_table(
        table_name='bots',
        column='training',
        value=False,
        where_condition=f'WHERE "user"={user} AND "id"={bot[0]}'
    )

@login_required
@endpoint.route('/set_stop_loss/<int:user>/<int:bot_id>/<float:stop_loss>', methods=['POST'])
def set_stop_loss(user: int, bot_id: int, stop_loss: float) -> dict:
    """
    Updates the stop loss value for a specific bot in the database.

    Parameters:
    - user (int): The ID of the user who owns the bot.
    - bot_id (int): The ID of the bot for which the stop loss value needs to be updated.
    - stop_loss (float): The new stop loss value to be set for the bot.

    Returns:
    - dict: A dictionary containing a single key-value pair, where the key is 'success' and the value is True.

    This function is decorated with @login_required, ensuring that only authenticated users can access this route.
    The stop loss value is updated in the 'bots' table of the database using the provided user ID and bot ID.
    """
    postgres_db.update_table('bots', 'stop_loss', stop_loss, f"""WHERE "user"={user} AND "id"={bot_id}""")
    return {'success': True}

@login_required
@endpoint.route('/get_stop_loss/<int:user>/<int:bot_id>', methods=['GET'])
def get_stop_loss(user: int, bot_id: int) -> dict:
    """
    Retrieves the stop loss value for a specific bot from the database.

    Parameters:
    - user (int): The ID of the user who owns the bot.
    - bot_id (int): The ID of the bot for which the stop loss value needs to be retrieved.

    Returns:
    - dict: The function returns the stop loss value as a JSON string.

    This function is decorated with @login_required, ensuring that only authenticated users can access this route.
    The stop loss value is retrieved from the 'bots' table of the database using the provided user ID and bot ID.
    The retrieved stop loss value is then converted to a JSON string and returned.
    """
    query = f"""SELECT stop_loss FROM bots WHERE "user"={user} AND "id"={bot_id}"""
    query_response: pd.DataFrame = postgres_db.execute_read_query(query, return_type='pd.DataFrame')
    stop_loss = query_response.loc[0];
    return stop_loss.to_json()

@login_required
@endpoint.route('/set_stop_loss_trailing/<int:user>/<int:bot_id>/<string:trailing>', methods=['POST'])
def set_stop_loss_trailing(user: int, bot_id: int, trailing: str) -> dict:
    """
    Updates the stop loss trailing value for a specific bot in the database.

    Parameters:
    - user (int): The ID of the user who owns the bot.
    - bot_id (int): The ID of the bot for which the stop loss trailing value needs to be updated.
    - trailing (str): The new stop loss trailing value to be set for the bot. It should be either 'true' or 'false'.

    Returns:
    - dict: A dictionary containing a single key-value pair, where the key is 'success' and the value is True.

    This function is decorated with @login_required, ensuring that only authenticated users can access this route.
    The stop loss trailing value is updated in the 'bots' table of the database using the provided user ID and bot ID.
    """
    trailing: bool = trailing.lower() == 'true'
    postgres_db.update_table('bots', 'stop_loss_trailing', trailing, f"""WHERE "user"={user} AND "id"={bot_id}""")
    return {'success': True}

@login_required
@endpoint.route('/get_trailing/<int:user>/<int:bot_id>', methods=['GET'])
def get_stop_loss_trailing(user: int, bot_id: int) -> dict:
    """
    Retrieves the stop loss trailing value for a specific bot from the database.

    Parameters:
    - user (int): The ID of the user who owns the bot.
    - bot_id (int): The ID of the bot for which the stop loss trailing value needs to be retrieved.

    Returns:
    - dict: The function returns the stop loss trailing value as a JSON string.

    This function is decorated with @login_required, ensuring that only authenticated users can access this route.
    The stop loss trailing value is retrieved from the 'bots' table of the database using the provided user ID and bot ID.
    The retrieved stop loss trailing value is then converted to a JSON string and returned.
    """
    query = f"""SELECT stop_loss_trailing FROM bots WHERE "user"={user} AND "id"={bot_id}"""
    query_response: pd.DataFrame = postgres_db.execute_read_query(query, return_type='pd.DataFrame')
    stop_loss_trailing = query_response.loc[0];
    return stop_loss_trailing.to_json()

@login_required
@endpoint.route('/set_take_profit/<int:user>/<int:bot_id>/<float:take_profit>', methods=['POST'])
def set_take_profit(user: int, bot_id: int, take_profit: float) -> dict:
    """
    Updates the take profit value for a specific bot in the database.

    Parameters:
    - user (int): The ID of the user who owns the bot.
    - bot_id (int): The ID of the bot to update.
    - take_profit (float): The new take profit value to set for the bot.

    Returns:
    - dict: A dictionary containing a single key-value pair.
        - 'success': A boolean value indicating whether the update was successful.

    This function is decorated with `@login_required` to ensure that only authenticated users can access this route.
    It updates the take profit value for the specified bot in the database using the provided user ID and bot ID.
    """
    postgres_db.update_table('bots', 'take_profit', take_profit, f"""WHERE "user"={user} AND "id"={bot_id}""")
    return {'success': True}

@login_required
@endpoint.route('/get_take_profit/<int:user>/<int:bot_id>', methods=['GET'])
def get_take_profit(user: int, bot_id: int) -> dict:
    """
    Retrieves the take profit value for a specific bot from the database.

    Parameters:
    - user (int): The ID of the user who owns the bot. This parameter is expected to be an integer.
    - bot_id (int): The unique identifier of the bot. This parameter is expected to be an integer.

    Returns:
    - dict: The function returns the take profit value as a JSON string.

    Note:
    - This function is decorated with `@login_required` to ensure that only authenticated users can access this route.
    - The take profit value is retrieved from the database using the provided user ID and bot ID.
    - The retrieved take profit value is then converted to a JSON string and returned.
    """
    query = f"""SELECT take_profit FROM bots WHERE "user"={user} AND "id"={bot_id}"""
    query_response: pd.DataFrame = postgres_db.execute_read_query(query, return_type='pd.DataFrame')
    take_profit = query_response.loc[0];
    return take_profit.to_json()

@login_required
@endpoint.route('/bot/<int:bot_id>')
def bot(bot_id: int) -> render_template:
    """
    This function retrieves and displays the details of a specific bot.

    Parameters:
    - bot_id (int): The unique identifier of the bot. This parameter is expected to be an integer.

    Returns:
    - render_template: A Flask function that renders a template with the provided arguments.
        - 'bot.html': The name of the template file to render.
        - user: The current user object.
        - bot: A list containing information about the bot, including its ID, model type, etc.

    This function is decorated with @login_required, which ensures that only authenticated users can access this route.
    The bot's details are retrieved from the database using the provided bot_id and then rendered in the 'bot.html' template.
    """
    # TODO Make sure that the requested bot belongs to the current user
    
    bot = postgres_db.get_bot_by_id(bot_id)
    trades = postgres_db.get_trades(current_user.get_id(), bot_id, 50)
    return render_template('bot.html', user=current_user, bot=bot, trades=trades)


@login_required
@endpoint.route('/delete_bot/<int:bot_id>')
def bot_delete(bot_id: int) -> redirect:
    """
    Deletes a bot from the database based on the provided bot ID.

    Parameters:
    - bot_id (int): The unique identifier of the bot to be deleted. This parameter is expected to be an integer.

    Returns:
    - redirect: A Flask function that redirects the user to a different URL.
        - '/bot_overview': The URL to redirect the user to after successfully deleting the bot.

    Note:
    - This function is decorated with @login_required, which ensures that only authenticated users can access this route.
    - Before deleting the bot, a TODO comment suggests checking if the bot is currently running. This functionality is not implemented in the provided code.
    """
    postgres_db.delete_bot_by_id(bot_id)
    return redirect('/bot_overview')


@login_required
@endpoint.route('/bot_overview', methods=['GET'])
def bot_overview():
    """
    This function handles the display of all bots owned by the current user.
    It retrieves the list of bots from the database and renders a template with the bot details.

    Parameters:
    - request: A Flask request object containing information about the HTTP request.
        - method: The HTTP method used for the request. In this case, it should be 'GET'.

    Returns:
    - render_template: A Flask function that renders a template with the provided arguments.
        - 'bot_overview.html': The name of the template file to render.
        - user: The current user object.
        - bots: A list of dictionaries, where each dictionary represents a bot owned by the current user.
            Each bot dictionary contains information such as 'id', 'name', 'symbol', 'timeframe', 'model_type', etc.

    Note:
    - This function is decorated with @login_required, which ensures that only authenticated users can access this route.
    - The function checks the HTTP method of the request. If it is 'GET', it retrieves the list of bots from the database
      and renders the 'bot_overview.html' template with the bot details.
    """
    if request.method == 'GET':
        bots = postgres_db.get_all_bots_by_user(current_user.get_id())
        no_bots_created: bool = False
        if not bots:
            no_bots_created: bool = True
            bots: list[list[str]] = [['' for _ in range(8)]]
            bots[0][3] = 'You have not created a bot yet.'
        return render_template('bot_overview.html', user=current_user, bots=bots, no_bots_created=no_bots_created)


@login_required
@endpoint.route('/bot_creation', methods=['GET', 'POST'])
def bot_creation():
    """
    Handles the creation of a new bot. It processes both GET and POST requests.
    For GET requests, it renders the bot creation form.
    For POST requests, it processes the form data and creates a new bot in the database.

    Parameters:
    - request: A Flask request object containing information about the HTTP request.
        - method: The HTTP method used for the request. In this case, it should be either 'GET' or 'POST'.

    Returns:
    - render_template: A Flask function that renders a template with the provided arguments.
        - 'bot_creation.html': The name of the template file to render.
        - user: The current user object.
    - redirect: A Flask function that redirects the user to a different URL.
        - '/bot_overview': The URL to redirect the user to after successfully creating a new bot.
    """
    if request.method == 'GET':
        return render_template('bot_creation.html', user=current_user)
    if request.method == 'POST':
        params: dict = request.form.to_dict()

        technical_indicators: list[str] = [params.get(key) for key in params.keys() if 'technical_indicator' in key]
        technical_indicators: str = ','.join(technical_indicators)

        if params.get('hyperparamCheckbox') != 'on':
            hyper_parameters: dict = {
                "num_trees" : params.get('num_trees') if params.get('num_trees') else None,
                "max_depth" : params.get('max_depth') if params.get('max_depth') else None,
                "learning_rate" : params.get('learning_rate') if params.get('learning_rate') else None,
                "gamma" : params.get('gamma') if params.get('gamma') else None,
                "colsample_bytree" : params.get('colsample_bytree') if params.get('colsample_bytree') else None
            }
            hyper_parameters = json.dumps(hyper_parameters)
        else:
            hyper_parameters = json.dumps({})

        new_id = postgres_db.provide_unique_id('bots')

        postgres_db.insert_new_bot(
            new_id=new_id,
            user=current_user.get_id(),
            name=request.form.get('name'),
            symbol=request.form.get('crypto_currency'),
            timeframe=int(request.form.get('time_frame')),
            model_type=request.form.get('ml_model'),
            technical_indicators=technical_indicators,
            hyper_parameters=hyper_parameters,
            money=request.form.get('money')
        )

        return redirect('/bot_overview')


@endpoint.route('/dashboard')
def dashboard():
    """
    This function renders the dashboard page with the current user's information and a default symbol.

    Parameters:
    - None

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
            new_user_id = postgres_db.provide_unique_id(table='user')
            new_user = User(id=new_user_id, email=email, first_name=first_name, last_name=last_name, password=generate_password_hash(password1))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('endpoints.dashboard'))

    return render_template("sign_up.html", user=current_user)
