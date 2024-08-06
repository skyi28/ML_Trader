"""
This python module contains functions to receive data via the Bybit API.
"""
import os
import sys
basedir = os.path.abspath(os.path.dirname(__file__)) + os.sep
basedir_split = basedir.split(os.sep)
path_to_config = ''
for part in basedir_split:
    path_to_config += part + os.sep
    if part == "ML_Trader":
        path_to_config += f'{os.sep}config'
        break
sys.path.append(path_to_config)

import requests 
import json 
import time
import datetime 
import pandas as pd
from infrastructure.technical_indicators import TechnicalIndicators
from infrastructure.database import Database
from config.config import load_config
from infrastructure.logger import create_logger

class BybitData:
    def __init__(self) -> None:
        """
        Initialize the BybitData class.

        This class is responsible for fetching and processing data from Bybit API.
        It includes methods for fetching current prices, historical data, and calculating technical indicators.

        Attributes:
        - current_price_url (str): The URL for fetching current prices from Bybit API.
        - hist_prices_url (str): The URL for fetching historical prices from Bybit API.
        - logger (Logger): The logger object for logging errors and information.
        - config (dict): The configuration settings loaded from the config file.
        - ti (TechnicalIndicators): The instance of the TechnicalIndicators class for calculating technical indicators.
        - db (Database): The instance of the Database class for interacting with the database.
        - technical_indicators_function_mapping (dict): A dictionary mapping the names of technical indicators to their corresponding functions in the TechnicalIndicators class.
        """
        self.current_price_url = "https://api.bybit.com/v5/market/tickers"
        self.hist_prices_url = "https://api.bybit.com/v5/market/mark-price-kline"
        self.logger = create_logger('bybit_data.log')
        self.config = load_config(f'{path_to_config}{os.sep}config.yaml')
        self.ti = TechnicalIndicators()
        self.db = Database()
        
        self.technical_indicators_function_mapping = {
            "moving_average": self.ti.calc_moving_average,
            "exponential_moving_average": self.ti.calc_exponential_moving_average,
            "moving_std": self.ti.calc_moving_std,
            "periodic_highs": self.ti.calc_periodic_highs,
            "periodic_lows": self.ti.calc_periodic_lows,
            "bollinger_bands": self.ti.calc_bollinger_bands,
            "macd": self.ti.calc_macd,
            "rsi": self.ti.calc_rsi,
            "momentum": self.ti.calc_momentum
        }
        
    def get_data_thread(self):
        """
        This function is responsible for continuously fetching and updating data from Bybit API.
        It runs in an infinite loop, updating data at regular intervals.

        Parameters:
        - None

        Returns:
        - None
        """
        last_update_timestamp = -1
        self.logger.info(f'Starting data thread: {datetime.datetime.now()}')
        # TODO Check what the last timestamp in the database is and automatically update the data if necessary
        while True:
            try:
                # Update data as soon as bar closed
                if datetime.datetime.now().second == 0:
                    for symbol in self.config.tradeable_symbols:
                        hist_data = self.get_historic_data(symbol=symbol, limit=100)
                        self.insert_historical_data(symbol=symbol, data=hist_data)
                        
                # Update current price each second
                if last_update_timestamp + self.config.price_update_interval < time.time():
                    for symbol in self.config.tradeable_symbols:
                        latest_data = self.get_current_price(symbol=symbol)
                        self.insert_latest_data(data=latest_data)
                    last_update_timestamp = time.time()
            except Exception as e:
                self.logger.error(f'Error in data thread: {str(e)}')
    
    def get_current_price(self, symbol="BTCUSD") -> float:
        """
        Fetch the current price of a specified symbol from Bybit API.

        Parameters:
        - symbol (str): The symbol of the asset. Default is "BTCUSD".

        Returns:
        - tuple: A tuple containing the symbol, current timestamp, last price, bid price, ask price, bid size, ask size, and price change percentage in the last 24 hours.
        """
        params = {"category": "inverse", "symbol": symbol}
        response = json.loads(requests.get(self.current_price_url, params).text)
        last_price = float(response["result"]["list"][0]["lastPrice"])
        bid_price = float(response["result"]["list"][0]["bid1Price"])
        ask_price = float(response["result"]["list"][0]["ask1Price"])
        bid_size = float(response["result"]["list"][0]["bid1Size"])
        ask_size = float(response["result"]["list"][0]["ask1Size"])
        price_change_24h = float(response["result"]["list"][0]["price24hPcnt"])
        
        return symbol, datetime.datetime.now(), last_price, bid_price, ask_price, bid_size, ask_size, price_change_24h
    
    def get_data_helper(self, start: datetime.datetime = None, end: datetime.datetime = None, symbol: str = "BTCUSD", interval: str = "1", limit: int = 1_000) -> pd.DataFrame:
        """
        helper function for get_data function. Use get_data to receive data for a given symbol from Bybit.

        Parameters
        - start (datetime.datetime): The start date of the data
        - end (datetime.datetime): The end date of the data
        - symbol (str), optional: The symbol of the asset, by default "BTCUSD"
        - interval (str), optional: The interval of the data, by default "1"
        - limit (int), optional: The maximum number of data points to retrieve, by default 1000

        Returns
        - (pd.DataFrame) A pandas dataframe containing the historical data
        """
        params = {"category":"inverse","symbol":symbol,"interval":interval, "limit":limit}
        if start and end:
            start = int(start.timestamp() * 1000)
            end = int(end.timestamp() * 1000)
            params["start"] = start
            params["end"] = end
        response_hist_price = json.loads(requests.get(self.hist_prices_url, params).text)
        response_hist_price = response_hist_price["result"]["list"]
        
        timestamps = reversed([pd.to_datetime(datetime.datetime.fromtimestamp(int(response_hist_price[i][0][:-3]))) for i in range(len(response_hist_price))])
        open_prices = reversed([float(response_hist_price[i][1]) for i in range(len(response_hist_price))])
        close_prices = reversed([float(response_hist_price[i][4]) for i in range(len(response_hist_price))])
        
        data = pd.DataFrame({"Timestamp":timestamps, "Open": open_prices, "Close": close_prices})
        data["Timestamp"] = pd.to_datetime(data["Timestamp"])
        data.dropna(inplace=True)
        return data
    
    def get_historic_data(self, start: datetime.datetime = None, end: datetime.datetime = None, 
                          symbol: str ="BTCUSD", interval: str = "1", limit: int = 1_000, 
                          calc_technical_indicators: bool = True) -> pd.DataFrame:
        """
        Helper function for get_data function. Use get_data to receive data for a given symbol from Bybit.

        Parameters
        - start (datetime.datetime), optional: The start date of the data. Default is None.
        - end (datetime.datetime), optional: The end date of the data. Default is None.
        - symbol (str), optional: The symbol of the asset. Default is "BTCUSD".
        - interval (str), optional: The interval of the data. Default is "1".
        - limit (int), optional: The maximum number of data points to retrieve. Default is 1000.

        Returns
        - (pd.DataFrame): A pandas dataframe containing the historical data.
        """
        data = []
        try:
            if start and end:
                next_end = start + datetime.timedelta(minutes=int(interval)*limit)
                data.append(self.get_data_helper(start, next_end, symbol, interval, limit))
            
                while data[-1]["Timestamp"].iloc[-1] < end:
                    next_start = data[-1]["Timestamp"].iloc[-1] + datetime.timedelta(minutes=int(interval))
                    next_end = next_start + datetime.timedelta(minutes=int(interval)*limit)
                    data.append(self.get_data_helper(symbol, next_start, next_end, symbol, interval, limit))
            else:
                data.append(self.get_data_helper(symbol=symbol, interval=interval, limit=limit))
        except Exception as e:
            self.logger.error(f"Error retrieving data for {symbol} from Bybit. \n{e}")
            return None
            
        data = pd.concat(data, axis=0)
        data.reset_index(inplace=True, drop=True)
        if end:
            data = data.loc[data["Timestamp"] <= end]
        self.logger.info(f"{len(data)} data points retrieved for {symbol} from {start} to {end}.")
        
        if calc_technical_indicators:
            for indicator in self.config.technical_indicators.indicators:
                try:
                    function = self.technical_indicators_function_mapping.get(indicator)
                    if indicator == "bollinger_bands":
                        data['lower_bollinger_band'], data['upper_bollinger_band'] = function(data['Open'])
                    else:
                        data[indicator] = function(data['Open'])
                except Exception as e:
                    self.logger.error(f"Error calculating technical indicator {indicator} for {symbol}. \n{e}")
            data.dropna(inplace=True)
            data.reset_index(inplace=True, drop=True)
        
        return data
    
    def insert_historical_data(self, symbol: str, data: pd.DataFrame) -> None:
        """
        Inserts historical data into the database.

        This function constructs an SQL query to insert historical data into a specified table in the database.
        If a record with the same timestamp already exists, it updates the existing record with the new data.

        Parameters:
        - symbol (str): The symbol of the asset for which the data is being inserted.
        - data (pd.DataFrame): A pandas DataFrame containing the historical data to be inserted.
            The DataFrame should have columns corresponding to the database table columns.

        Returns:
        - None
        """
        query: str = f"INSERT INTO {symbol} ("
        for col in data.columns:
            query += f"{col},"
        query = query[:-1]  # remove last comma
        
        query += ") VALUES ("
        for col in data.columns:
            query += f"%s,"
        query = query[:-1]  # remove last comma
        
        # TODO This query can be optimized by only updating the technical indicators
        query += ') ON CONFLICT ("timestamp") DO UPDATE SET '
        for col in data.columns:
            query += f"{col} = %s,"
        query = query[:-1]  # remove last comma
        
        for idx, row in data.iterrows():
            row = tuple(row) + tuple(row)
            rows_affected = self.db.execute_write_query(query, row)
            if not rows_affected:
                break
        self.db.commit()
        
    def insert_latest_data(self, data: tuple) -> None:
        """
        Inserts the latest price data into the 'prices' table in the database.

        This function constructs an SQL query to insert the latest price data into the 'prices' table.
        If a record with the same symbol already exists, it updates the existing record with the new data.

        Parameters:
        - data (tuple): A tuple containing the following data:
            symbol (str): The symbol of the asset.
            timestamp (datetime.datetime): The timestamp of the data.
            last_price (float): The last price of the asset.
            bid_price (float): The bid price of the asset.
            ask_price (float): The ask price of the asset.
            bid_size (float): The bid size of the asset.
            ask_size (float): The ask size of the asset.
            price_change_last_24h (float): The price change percentage in the last 24 hours.

        Returns:
        - None
        """
        query: str = f'INSERT INTO prices (symbol, "timestamp", last_price, bid_price, ask_price, bid_size, ask_size, price_change_last_24h)'
        query += f' VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
        query += f' ON CONFLICT (symbol) DO UPDATE SET'
        query += f' symbol = %s,'
        query += f' "timestamp" = %s,'
        query += f' last_price = %s,'
        query += f' bid_price = %s,'
        query += f' ask_price = %s,'
        query += f' bid_size = %s,'
        query += f' ask_size = %s,'
        query += f' price_change_last_24h = %s'
        
        row = tuple(data) + tuple(data)
        self.db.execute_write_query(query, row)
        self.db.commit()              
        