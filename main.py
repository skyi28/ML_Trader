"""
This file is the main entry point for the ML Trader application. It performs the following tasks:

1. Sets up the necessary paths and imports required modules.
2. Loads the configuration settings from the config.yaml file.
3. Establishes a connection to the database.
4. Creates historical price tables for each tradeable symbol in the configuration.
5. Creates a table to store the latest prices for each tradeable symbol.
6. Starts a separate thread to fetch and process data from the ByBit API.
7. Creates a user table in the database.
8. Starts a separate thread to create predictions for all running models.
9. Starts the web application using Flask.
"""
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
import subprocess

from config.config import load_config
from infrastructure.database import Database
from infrastructure.bybit_data import BybitData
from models.execute_models import ExecuteModels
from infrastructure.logger import create_logger
from website.app import create_app

logger = create_logger('startup.log')
logger.info('Starting ML Trader...')

logger.info(f'Loading config.yaml from {path_to_config}{os.sep}config{os.sep}config.yaml')
config = load_config(f'{path_to_config}{os.sep}config{os.sep}config.yaml')

# Execute cmd commands to start the database
# change_dir_command: str = f'cd {config.postgres.path_to_postgres}{os.sep}bin'
# start_postgres_command: str = f'.{os.sep}pg_ctl.exe start -D "A:{os.sep}PostgreSQL{os.sep}16{os.sep}data"' # Replace this with path_to_postgres
# logger.info(f'Starting postgres...')
# result = subprocess.run(['powershell', '-Command',f'{change_dir_command}; {start_postgres_command}'])
# logger.info(f'Output: {result.stdout} \nError: {result.stderr}')

# Linux
def start_postgres():
    try:
        # Run the command to start PostgreSQL service
        subprocess.run(['sudo', '-S', 'service', 'postgresql', 'start'], input=f'{config.sudo_password}', check=True, text=True)
        print("PostgreSQL service started successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to start PostgreSQL service: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Call the function to start PostgreSQL
start_postgres()


# Wait until postgres is running
# time.sleep(10)

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
    db.create_table(symbol, column_names_and_types, unique_constraints, create_index_column='timestamp')
    
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

# Create bots table
db.create_table('bots', ['id INT', '"user" INT', 'name VARCHAR', 'created TIMESTAMP', 'last_trained TIMESTAMP', 'symbol VARCHAR', 'timeframe INT', 'model_type VARCHAR', 'technical_indicators VARCHAR', 'hyper_parameters JSON', 'training BOOL', 'training_set_percentage FLOAT', 'training_error_metrics JSON', 'running BOOL', 'prediction FLOAT', 'position VARCHAR', 'entry_price FLOAT', 'money FLOAT', 'stop_loss FLOAT', 'stop_loss_trailing BOOL', 'take_profit FLOAT'], primary_keys=['id'])

# Create trades table
db.create_table('trades', ['trade_id INT', '"user" INT', 'bot_id INT', '"timestamp" TIMESTAMP', 'symbol VARCHAR', 'side VARCHAR', 'entry_price FLOAT', 'close_price FLOAT', 'money FLOAT', 'profit_abs FLOAT', 'profit_rel FLOAT', 'trading_fee FLOAT', 'tp_trigger BOOL', 'sl_trigger BOOL'], primary_keys=['trade_id'], create_index_column='timestamp')

logger.info('Starting model prediction thread')
db.execute_write_query("UPDATE bots SET position='neutral'")
db.commit()
em = ExecuteModels()
model_prediction_thread = threading.Thread(target=em.prediction_loop)
model_prediction_thread.start()

logger.info('Start web application')
app = create_app()
# Start web application - works only if this is the main thread 
app.run(host=config.webserver.host, 
                    debug=config.webserver.debug_mode, 
                    port=config.webserver.port, 
                    ssl_context='adhoc')
