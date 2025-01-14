from flask import Blueprint, render_template, redirect, flash, request, url_for
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import json
import datetime
import numpy as np
import pandas as pd

from website.user import User
from website.app import db
from infrastructure.database import Database


api = Blueprint('api', __name__)

postgres_db = Database()

# TODO Include a check if the user who send the request is allowed to execute the method for the requested bot

@login_required
@api.route('/api/chart_data')
def chart_data() -> dict:
    """
    This function retrieves the last 'entries' number of closing prices for a given symbol from a PostgreSQL database.
    It then formats the data into a dictionary and returns it as a JSON string.

    Parameters:
    - symbol (str): The symbol for which the closing prices are to be retrieved.
    - entries (int): The number of closing prices to retrieve.

    Returns:
    - dict: A dictionary containing the symbol, dates, and price data. The dates are formatted as '%d.%m.%Y %H:%M:%S'.
    """
    # TODO Error handling
    symbol: str = request.args.get('symbol')
    entries: int = int(request.args.get('entries'))
    # TODO Rewrite entries to be timeframes instead and change the SQL query to something like SELECT price WHERE timestamp >= TO_DATE(...)
    # Check if that makes sense due to the loss of trades which are shown then...
    
    return_trades: bool = eval(request.args.get('return_trades'))
    
    # TODO Check if this query can be optimized by deleting the ORDER BY statement and then reversing the list
    query_result: list = postgres_db.execute_read_query(f"SELECT timestamp, close FROM {symbol.lower()} ORDER BY timestamp DESC LIMIT {entries}")
    dates = [data[0].strftime('%d.%m.%Y %H:%M:%S') for data in query_result]
    dates.reverse()
    price_data = [data[1] for data in query_result]
    price_data.reverse()
    result: dict = {
        'symbol': symbol,
        'dates': dates,
        'price_data': price_data,
    }
    
    if return_trades:
        user: int = int(request.args.get('user'))
        bot_id: int = int(request.args.get('bot_id'))
        min_date: datetime.datetime = dates[0]
        
        trades: pd.DataFrame = postgres_db.get_trades_for_plotting(user, bot_id, min_date)
        prices: pd.DataFrame = pd.DataFrame()
        prices['timestamp'] = pd.to_datetime(dates, format='mixed')
        
        short_trades_indexes = []
        long_trades_indexes = []

        short_trade_entry_prices = []
        long_trade_entry_prices = []

        for _, trade in trades.iterrows():
            trade_time = trade['timestamp']
            trade_time: str = datetime.datetime.strftime(trade_time, '%Y-%d-%m %H:%M:%S') 
            trade_time = pd.to_datetime(trade_time)
            price_time_diff = (prices['timestamp'] - trade_time).abs()
            closest_price_index = price_time_diff.idxmin()

            if trade['side'] == 'short':
                short_trades_indexes.append(closest_price_index)
                short_trade_entry_prices.append(trade['entry_price'])
            elif trade['side'] == 'long':
                long_trades_indexes.append(closest_price_index)
                long_trade_entry_prices.append(trade['entry_price'])
                
        additional_trade_info: dict = {
            'short_trades_indexes': short_trades_indexes,
            'long_trades_indexes': long_trades_indexes,
            'short_trade_entry_prices': short_trade_entry_prices,
            'long_trade_entry_prices': long_trade_entry_prices
        }
        
        result.update(additional_trade_info)
    
    return json.dumps(result)

@login_required
@api.route('/api/get_money_development_data/<int:user>/<int:bot_id>', methods=['GET'])
def get_money_development_data(user: int, bot_id: int) -> dict:
    query: str = f'SELECT timestamp, money FROM trades WHERE "user"={user} AND bot_id={bot_id} ORDER BY timestamp DESC'
    query_result: pd.DataFrame = postgres_db.execute_read_query(query)

    dates = [data[0].strftime('%d.%m.%Y %H:%M:%S') for data in query_result]
    dates.reverse()
    money_data = [data[1] for data in query_result]
    money_data.reverse()

    result: dict = {
        'dates': dates,
        'money': money_data,
    }

    return json.dumps(result)
    
@login_required
@api.route('/api/last_price')
def get_last_price() -> dict:
    """
    Retrieves the last price for a given symbol from a PostgreSQL database.

    Parameters:
    - symbol (str): The symbol for which the last price is to be retrieved.

    Returns:
    - dict: A JSON string representing the last price data for the given symbol.
    The JSON string contains the following keys: 'symbol', 'timestamp', and 'price'.
    """
    symbol: str = request.args.get('symbol')
    query_result: pd.DataFrame = postgres_db.execute_read_query(f"SELECT * FROM prices WHERE symbol='{symbol}' ORDER BY timestamp DESC LIMIT 1", return_type="pd.DataFrame")
    query_result = query_result.loc[0]
    return query_result.to_json()

@login_required
@api.route('/api/bot_training_status/<int:user>/<int:bot_id>')
def get_bot_training_status(user: int, bot_id: int) -> dict:
    """
    Retrieves the training status of a specific bot for a given user from a PostgreSQL database.

    Parameters:
    - user (int): The unique identifier of the user.
    - bot_id (int): The unique identifier of the bot.

    Returns:
    - dict: A JSON string representing the training status of the bot.
    The JSON string contains a single key-value pair: 'training', which holds the training status (True or False).
    """
    query_result: pd.DataFrame = postgres_db.execute_read_query(f'SELECT training FROM bots WHERE "user"={user} AND id={bot_id}', return_type='pd.DataFrame')
    result = json.dumps({"training": str(query_result['training'].iloc[0])})
    return result

@login_required
@api.route('/api/bot_training_error_metrics/<int:user>/<int:bot_id>')
def get_bot_training_error_metrics(user: int, bot_id: int) -> dict:
    """
    Retrieves the training error metrics for a specific bot for a given user from a PostgreSQL database.

    Parameters:
    - user (int): The unique identifier of the user. This parameter is used to identify the user in the database.
    - bot_id (int): The unique identifier of the bot. This parameter is used to identify the bot in the database.

    Returns:
    - dict: A JSON string representing the training error metrics of the bot.
    """
    query_result: dict = postgres_db.get_training_error_metrics(user=user, model_id=bot_id)
    result = json.dumps(query_result)
    return result

@login_required
@api.route('api/bot_is_running/<int:user>/<int:bot_id>')
def bot_is_running(user: int, bot_id: int) -> str:
    """
    This function checks if a specific bot for a given user is currently running in a PostgreSQL database.

    Parameters:
    - user (int): The unique identifier of the user. This parameter is used to identify the user in the database.
    - bot_id (int): The unique identifier of the bot. This parameter is used to identify the bot in the database.

    Returns:
    - str: A JSON string representing the running status of the bot.
    The JSON string contains a single key-value pair: 'running', which holds the running status (True or False).
    """
    # TODO Error handling
    query: str = f'SELECT running FROM bots WHERE "user"={user} AND "id"={bot_id}'
    query_result = postgres_db.execute_read_query(query, return_type='pd.DataFrame')
    result: dict = {'running': str(query_result['running'].iloc[0])}
    return json.dumps(result)

@login_required
@api.route('/api/data_for_trades_histogram/<int:user>/<int:bot_id>/<int:number_of_bins>')
def get_data_for_trades_histogram(user: int, bot_id: int, number_of_bins: int) -> dict:
    """
    Retrieves all trades for a specific bot for a given user from a PostgreSQL database.

    Parameters:
    - user (int): The unique identifier of the user. This parameter is used to identify the user in the database.
    - bot_id (int): The unique identifier of the bot. This parameter is used to identify the bot in the database.

    Returns:
    - dict: A JSON string representing all trades for the bot.
    """
    query: str = f'SELECT profit_rel FROM trades WHERE "user"={user} AND "bot_id"={bot_id}'
    query_result: pd.DataFrame = postgres_db.execute_read_query(query, return_type='pd.DataFrame')
    query_result['profit_rel'] = query_result['profit_rel'] * 100 # convert to percentage

    min_return: float = float(query_result['profit_rel'].min())
    max_return: float = float(query_result['profit_rel'].max())
    bin_width: float = (max_return - min_return) / (number_of_bins - 1)

    bins = []

    # If negative values exist
    if min_return < 0:
        # Find the largest multiple of bin_width less than or equal to min_return
        neg_start = -(-min_return // bin_width) * bin_width  # Equivalent to math.floor for negatives
        bins.extend([neg_start + bin_width * i for i in range(int(abs(neg_start) // bin_width) + 1)])

    # Add zero as a boundary if the range spans negative to positive
    if min_return < 0 < max_return:
        bins.append(0)

    # If positive values exist
    if max_return > 0:
        pos_start = 0 if min_return < 0 else min_return  # Start from 0 if range includes negatives
        bins.extend([pos_start + bin_width * i for i in range(1, int(max_return // bin_width) + 2)])

    # Ensure bins are unique and sorted
    bins = sorted(set(bins))

    binned_returns: pd.Series = query_result.groupby(pd.cut(query_result['profit_rel'], bins)).size()
    result: dict = {
        'bins': format_bin_return(binned_returns),
        'counts': binned_returns.values.tolist()
    }

    return json.dumps(result)

def format_bin_return(binned_returns, decimal_places: int = 3):
    binned_returns_formatted = []
    for i in range(len(binned_returns)):
        binned_return = str(binned_returns.keys()[i]).split(',')
        binned_return = str(binned_return[0]) + '% ' + str(binned_return[1]) + '%'
        binned_return = binned_return.replace('(','').replace(']','').replace(' ', '')
        binned_return = binned_return.split('%')

        if binned_return[0].find('e') != -1:
            binned_return[0] = '0.'
            for i in range(decimal_places):
                binned_return[0] += '0'
        if binned_return[1].find('e') != -1:
            binned_return[1] = '0.'
            for i in range(decimal_places):
                binned_return[1] += '0'

        decimal_splitted = binned_return[0].split('.')
        if len(decimal_splitted[1]) < decimal_places:
            for i in range(decimal_places - len(decimal_splitted[1])):
                decimal_splitted[1] += '0'
        binned_return[0] = decimal_splitted[0] + '.' + decimal_splitted[1][0:decimal_places]
        

        decimal_splitted = binned_return[1].split('.')
        binned_return[1] = decimal_splitted[0] + '.' + decimal_splitted[1][0:decimal_places]
        if len(decimal_splitted[1]) < decimal_places:
            for i in range(decimal_places - len(decimal_splitted[1])):
                decimal_splitted[1] += '0'
        binned_return[1] = decimal_splitted[0] + '.' + decimal_splitted[1][0:decimal_places]

        binned_return = binned_return[0] +'% - '+ binned_return[1] + '%'
        binned_returns_formatted.append(binned_return)
    return binned_returns_formatted