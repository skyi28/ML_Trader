from flask import Blueprint, render_template, redirect, flash, request, url_for
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import pandas as pd

from website.user import User
from website.app import db
from infrastructure.database import Database


api = Blueprint('api', __name__)

postgres_db = Database()

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
     
    query_result: list = postgres_db.execute_read_query(f"SELECT timestamp,close FROM {symbol.lower()} ORDER BY timestamp DESC LIMIT {entries}")
    dates = [data[0].strftime('%d.%m.%Y %H:%M:%S') for data in query_result]
    dates.reverse()
    price_data = [data[1] for data in query_result]
    price_data.reverse()
    result: dict = {
        'symbol': symbol,
        'dates': dates,
        'price_data': price_data,
    }
    
    return json.dumps(result)
    
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
    return query_result.to_json()
