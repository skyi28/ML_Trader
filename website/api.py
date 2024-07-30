from flask import Blueprint, render_template, redirect, flash, request, url_for
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json

from website.user import User
from website.app import db
from infrastructure.database import Database


api = Blueprint('api', __name__)

postgres_db = Database()

@api.route('/api/chart_data')
def test():
    symbol: str = request.args.get('symbol')
    entries: int = int(request.args.get('entries'))
    
    
    query_result = postgres_db.execute_read_query(f"SELECT timestamp,close FROM {symbol.lower()} ORDER BY timestamp DESC LIMIT {entries}")
    # TODO also pass symbol
    dates = [data[0].strftime('%d.%m.%Y %H:%M:%S') for data in query_result]
    dates.reverse()
    price_data = [data[1] for data in query_result]
    price_data.reverse()
    # TODO reverse order of both arrays
    result: dict = {
        'symbol': symbol,
        'dates': dates,
        'price_data': price_data,
    }
    
    return json.dumps(result)
    