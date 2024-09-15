"""
This python module contains functions needed to let all running models make predictions.
# TODO Error handling --> if error close position? Maybe make it configurable...
"""
import os
basedir = os.path.abspath(os.path.dirname(__file__)) + os.sep
basedir_split = basedir.split(os.sep)
path_to_config = ''
for part in basedir_split:
    path_to_config += part + os.sep
    if part == "ML_Trader":
        path_to_config += f'{os.sep}config'
        break
    
import time
import datetime
import pandas as pd
import numpy as np
    
from config.config import load_config
from infrastructure.database import Database
from models.prepare_training_data import PrepareTrainingData
from models.xgboost_model import XGBoostModel

class ExecuteModels:
    def __init__(self) -> None:
        """
        Initialize the ExecuteModels class.

        This class is responsible for executing the prediction models and executing trades based on the predictions.

        Parameters:
        - None

        Returns:
        - None
        """
        self.config = load_config(f'{path_to_config}{os.sep}config.yaml')
        self.db: Database = Database()
        self.ptd: PrepareTrainingData = PrepareTrainingData()
        self.TRADING_FEE: float = float(self.config.trading_fees)
        
    def prediction_loop(self) -> None:
        """
        This function is responsible for executing the prediction models and executing trades based on the predictions.
        It runs in an infinite loop, checking every second if it's time to make predictions.

        Parameters:
        - self (ExecuteModels): The instance of the ExecuteModels class.

        Returns:
        - None
        """
        while True:
            # TODO Different models can have different time frames --> rewrite this function
            if datetime.datetime.now().second == 0:
                time.sleep(0.5) # TODO This makes sure that the data is available in the database. Write code which checks if the data is available and then execute the following code
                running_models = self.db.get_all_running_models()
                for _, row in running_models.iterrows():
                    prediction_features: pd.DataFrame = self.ptd.load_data_for_prediction(
                        symbol=row['symbol'],
                        feature_columns=row['technical_indicators'].split(',')
                    )
                    if row['model_type'].lower() == 'xgboost':
                        model_class = XGBoostModel()
                        model = model_class.load_model(row['user'], row['id'])

                    pred = model.predict(prediction_features)
                    pred = int(pred[0])

                    # TODO Delete this
                    pred = np.random.randint(0,2)

                    self.db.update_table(
                        table_name='bots',
                        column='prediction',
                        value=pred,
                        where_condition=f'WHERE "user"={row["user"]} AND "id"={row["id"]}'
                    )

                    self.execute_trades(row)

                    print(f'Model_{row["user"]}_{row["id"]} predicts for {row["symbol"]}: ', pred)

                    
    def execute_trades(self, row: pd.Series) -> None:
        """
        This function is responsible for executing trades based on the prediction results.
        It handles both long and short positions, and closes the positions based on the prediction results.
        It also updates the position, entry price, and logs trades.

        Parameters:
        - self (ExecuteModels): The instance of the ExecuteModels class.
        - row (pd.Series): A row from the DataFrame containing information about the running model, such as user, id, symbol, position, prediction, and entry price.

        Returns:
        - None
        """
        # Neutral position
        if row['position'] == 'neutral':
            # Open long position
            if row['prediction'] == 1:
                self.db.update_table(
                    table_name='bots',
                    column='position',
                    value='long',
                    where_condition=f'WHERE "user"={row["user"]} AND "id"={row["id"]}'
                )
                print(f'Model_{row["user"]}_{row["id"]} opened long position for {row["symbol"]}')

            # Open short position
            elif row['prediction'] == 0:
                self.db.update_table(
                    table_name='bots',
                    column='position',
                    value='short',
                    where_condition=f'WHERE "user"={row["user"]} AND "id"={row["id"]}'
                )
                print(f'Model_{row["user"]}_{row["id"]} opened short position for {row["symbol"]}')

            symbol: str = row["symbol"]
            # TODO Take into account bid and ask price
            close_price: float = self.db.execute_read_query(f"SELECT last_price FROM prices WHERE symbol='{symbol}' ORDER BY timestamp DESC LIMIT 1", return_type="pd.DataFrame")['last_price'].iloc[0]
            # Update entry price
            self.db.update_table(
                table_name='bots',
                column='entry_price',
                value=close_price,
                where_condition=f'WHERE "user"={row["user"]} AND "id"={row["id"]}'
            )

        # Long position
        if row['position'] == 'long':
            # Close long position
            if row['prediction'] == 0: # TODO stop loss or take profit conditions e.g. or close_price <= row['entry_price'] * (1 - self.config.trading.stop_loss_percentage):
                self.db.update_table(
                    table_name='bots',
                    column='position',
                    value='short',
                    where_condition=f'WHERE "user"={row["user"]} AND "id"={row["id"]}'
                )
                symbol: str = row["symbol"]
                # TODO Take into account bid and ask price
                close_price: float = self.db.execute_read_query(f"SELECT last_price FROM prices WHERE symbol='{symbol}' ORDER BY timestamp DESC LIMIT 1", return_type="pd.DataFrame")['last_price'].iloc[0]
                self.log_trade(row, close_price, 'long')
                print(f'Model_{row["user"]}_{row["id"]} closed long position for {row["symbol"]}')
                # Update entry price
                self.db.update_table(
                    table_name='bots',
                    column='entry_price',
                    value=close_price,
                    where_condition=f'WHERE "user"={row["user"]} AND "id"={row["id"]}'
                )
                # TODO Idea is to prevent the bot from opening and directly closing a position -> Check if that works
                return


        # Short position
        elif row['position'] =='short':
            # Close short position
            if row['prediction'] == 1: # TODO stop loss or take profit conditions e.g. or close_price >= row['entry_price'] * (1 + self.config.trading.stop_loss_percentage):
                self.db.update_table(
                    table_name='bots',
                    column='position',
                    value='long',
                    where_condition=f'WHERE "user"={row["user"]} AND "id"={row["id"]}'
                )

                symbol: str = row["symbol"]
                # TODO Take into account bid and ask price
                close_price: float = self.db.execute_read_query(f"SELECT last_price FROM prices WHERE symbol='{symbol}' ORDER BY timestamp DESC LIMIT 1", return_type="pd.DataFrame")['last_price'].iloc[0]
                self.log_trade(row, close_price, 'short')
                print(f'Model_{row["user"]}_{row["id"]} closed short position for {row["symbol"]}')

                # Update entry price
                self.db.update_table(
                    table_name='bots',
                    column='entry_price',
                    value=close_price,
                    where_condition=f'WHERE "user"={row["user"]} AND "id"={row["id"]}'
                )
                # TODO Idea is to prevent the bot from opening and directly closing a position -> Check if that works
                return

                
    def log_trade(self, row: pd.Series, close_price: float, closing_position: str) -> None:
        """
        Logs a trade by calculating the profit and printing relevant information.

        Parameters:
        - self (ExecuteModels): The instance of the ExecuteModels class.
        - row (pd.Series): A row from the DataFrame containing information about the running model, such as user, id, symbol, position, prediction, and entry price.
        - close_price (float): The price at which the trade was closed.
        - closing_position (str): The position that was closed ('long' or 'short').

        Returns:
        - None
        """
        # TODO Implement Kelly criterion
        invested_fraction = 1
        
        money: float = row['money']
        
        if closing_position == 'long':
            trade_diff: float = close_price - row['entry_price']
            profit_rel: float = float(trade_diff / row['entry_price']) - self.TRADING_FEE 
            profit_abs: float = money * profit_rel * invested_fraction
        elif closing_position == 'short':
            trade_diff: float = row['entry_price'] - close_price
            profit_rel: float = float(trade_diff / row['entry_price']) - self.TRADING_FEE
            profit_abs: float = money * profit_rel * invested_fraction
            
        money: float = money * (1 + profit_rel)
        
        self.db.update_table(
            table_name='bots',
            column='money',
            value=money,
            where_condition=f'WHERE "user"={row["user"]} AND "id"={row["id"]}'
            )
            
        self.db.insert_trade(
            user=row['user'],
            bot_id=row['id'],
            timestamp=datetime.datetime.now(),
            symbol=row['symbol'],
            side=closing_position,
            entry_price=row['entry_price'],
            close_price=close_price,
            money=money,
            profit_abs=profit_abs,
            profit_rel=profit_rel,
            trading_fee=self.TRADING_FEE,
            tp_trigger=False, # TODO Update when TP/SL was triggered
            sl_trigger=False  # TODO Update when TP/SL was triggered
        )

        print(f'Model_{row["user"]}_{row["id"]} Entry Price: {row["entry_price"]} Close Price: {close_price}')    
        print(f'Model_{row["user"]}_{row["id"]} Profit: {trade_diff}$ ({round(profit_rel, 5)})%')

            
            # TODO Save trade in database
            # TODO Update money
            # TODO Include trading fees
            # TODO Include Kelly criterion
                    