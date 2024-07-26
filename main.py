import os
import sys
basedir = os.path.abspath(os.path.dirname(__file__)) + os.sep
basedir_split = basedir.split(os.sep)
path_to_config = ''
for part in basedir_split:
    path_to_config += part + os.sep
    if part == "ML_Trader":
        break
sys.path.append(path_to_config)

import threading

from config.config import load_config
from infrastructure.database import Database
from infrastructure.bybit_data import BybitData
from infrastructure.logger import create_logger
from website.app import create_app

logger = create_logger('startup.log')
logger.info('Starting ML Trader...')

logger.info(f'Loading config.yaml from {path_to_config}{os.sep}config{os.sep}config.yaml')
config = load_config(f'{path_to_config}{os.sep}config{os.sep}config.yaml')

# TODO Execute cmd commands to start the database

logger.info('Establishing connection to database')
db = Database()

# Create historical price tables
for symbol in config.tradeable_symbols:
    logger.info(f'Creating historical price tables for {symbol}')
    column_names_and_types = ['"timestamp" TIMESTAMP', 'open FLOAT', 'close FLOAT']
    if len(config.technical_indicators.indicators) > 0:
        for indicator in config.technical_indicators.indicators:
            if indicator == 'bollinger_bands':
                column_names_and_types.append('"lower_bollinger_band" FLOAT')
                column_names_and_types.append('"upper_bollinger_band" FLOAT')
            else:
                column_names_and_types.append(f"{indicator} FLOAT")
    unique_constraints = ['"timestamp"']
    db.create_table(symbol, column_names_and_types, unique_constraints)
    
# Create latest price tables
for symbol in config.tradeable_symbols:
    logger.info(f'Creating latest price tables for {symbol}')
    column_names_and_types = ['symbol VARCHAR', '"timestamp" TIMESTAMP', 'last_price FLOAT', 'bid_price FLOAT', 'ask_price FLOAT', 'bid_size FLOAT', 'ask_size FLOAT', 'price_change_last_24h FLOAT']
    unique_constraints = ['symbol']
    db.create_table('prices', column_names_and_types, unique_constraints)
    
logger.info('Starting ByBit data thread')
bd = BybitData()
# Start data thread
data_thread = threading.Thread(target=bd.get_data_thread)
data_thread.start()

# Create user table
db.create_table('"user"', ['id INT','email VARCHAR','password VARCHAR','first_name VARCHAR','last_name VARCHAR'], primary_keys=['id'])

logger.info('Start web application')
app = create_app()
# Start web application - works only if this is the main thread 
app.run(host=config.webserver.host, 
                    debug=config.webserver.debug_mode, 
                    port=config.webserver.port, 
                    ssl_context='adhoc')