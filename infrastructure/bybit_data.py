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
import datetime 
import pandas as pd
from logger import create_logger

class BybitData:
    def __init__(self) -> None:
        self.current_price_url = "https://api.bybit.com/v5/market/tickers"
        self.hist_prices_url = "https://api.bybit.com/v5/market/mark-price-kline"
        self.logger = create_logger('bybit_data.log')
    
    def get_current_price(self, symbol="BTCUSD") -> float:
        """
        Get the current price of a given symbol on Bybit.

        Parameters
        ----------
        symbol : str, optional
            The symbol of the asset, by default "BTCUSD"

        Returns
        -------
        datetime.datetime
            The corresponding time
        float
            The current price of the asset

        Raises
        ------
        ValueError
            If the symbol is not valid

        Examples
        --------
        >>> from bybit_api import GetLiveBybitData
        >>> api = GetLiveBybitData()
        >>> time, current_price = api.get_current_price()
        >>> print(current_price)
        48500.0
        """
        params = {"category": "inverse", "symbol": symbol}
        response = json.loads(requests.get(self.current_price_url, params).text)
        last_price = float(response["result"]["list"][0]["lastPrice"])
        bid_price = float(response["result"]["list"][0]["bid1Price"])
        ask_price = float(response["result"]["list"][0]["ask1Price"])
        bid_size = float(response["result"]["list"][0]["bid1Size"])
        ask_size = float(response["result"]["list"][0]["ask1Size"])
        price_change_24h = float(response["result"]["list"][0]["price24hPcnt"])
        
        return datetime.datetime.now(), last_price, bid_price, ask_price, bid_size, ask_size, price_change_24h
    
    def get_data_helper(self, start:datetime.datetime, end:datetime.datetime, symbol="BTCUSD", interval="1", limit=1_000):
        """
        helper function for get_data function. Use get_data to receive data for a given symbol from Bybit.

        Parameters
        ----------
        start : datetime.datetime
            The start date of the data
        end : datetime.datetime
            The end date of the data
        symbol : str, optional
            The symbol of the asset, by default "BTCUSD"
        interval : str, optional
            The interval of the data, by default "1"
        limit : int, optional
            The maximum number of data points to retrieve, by default 1000

        Returns
        -------
        pd.DataFrame
            A pandas dataframe containing the historical data

        Examples
        --------
        >>> from bybit_api import GetLiveBybitData
        >>> api = GetLiveBybitData()
        >>> data = api.get_data(start=datetime.datetime(2022, 1, 1), end=datetime.datetime(2022, 1, 10))
        >>> print(data.head())
        Timestamp       Open       Close
        0  2022-01-04  48500.0000  48500.0000
        1  2022-01-05  48500.0000  48500.0000
        2  2022-01-06  48500.0000  48500.0000
        3  2022-01-07  48500.0000  48500.0000
        4  2022-01-08  48500.0000  48500.0000
        """
        start = int(start.timestamp() * 1000)
        end = int(end.timestamp() * 1000)
        params = {"category":"inverse","symbol":"BTCUSD","interval":interval, "limit":limit, "start":start, "end":end}
        response_hist_price = json.loads(requests.get(self.hist_prices_url, params).text)
        response_hist_price = response_hist_price["result"]["list"]
        
        timestamps = reversed([pd.to_datetime(datetime.datetime.fromtimestamp(int(response_hist_price[i][0][:-3]))) for i in range(len(response_hist_price))])
        open_prices = reversed([float(response_hist_price[i][1]) for i in range(len(response_hist_price))])
        close_prices = reversed([float(response_hist_price[i][4]) for i in range(len(response_hist_price))])
        
        data = pd.DataFrame({"Timestamp":timestamps, "Open": open_prices, "Close": close_prices})
        data["Timestamp"] = pd.to_datetime(data["Timestamp"])
        data.dropna(inplace=True)
        return data
    
    def get_data(self, start:datetime.datetime, end:datetime.datetime, symbol="BTCUSD", interval="1", limit=1_000):
        """
        Get  historical data for a given symbol on Bybit.

        Parameters
        ----------
        start : datetime.datetime
            The start date of the data
        end : datetime.datetime
            The end date of the data
        symbol : str, optional
            The symbol of the asset, by default "BTCUSD"
        interval : str, optional
            The interval of the data, by default "1" (1=1min,3,5,15,30,60,120,240,360,720,D,M,W)
        limit : int, optional
            The maximum number of data points to retrieve, by default 1000

        Returns
        -------
        pd.DataFrame
            A pandas dataframe containing the historical data

        Raises
        ------
        ValueError
            If the symbol or interval is not valid

        Examples
        --------
        >>> from bybit_api import GetLiveBybitData
        >>> api = GetLiveBybitData()
        >>> data = api.get_all_data(start=datetime.datetime(2022, 1, 1), end=datetime.datetime(2022, 1, 10))
        >>> print(data.head())
            Timestamp       Open       Close
        0  2022-01-04  48500.0000  48500.0000
        1  2022-01-05  48500.0000  48500.0000
        2  2022-01-06  48500.0000  48500.0000
        3  2022-01-07  48500.0000  48500.0000
        4  2022-01-08  48500.0000  48500.0000
        """
        next_end = start + datetime.timedelta(minutes=int(interval)*limit)
        data = []
        data.append(self.get_data_helper(start, next_end, symbol, interval, limit))
        
        try:
            while data[-1]["Timestamp"].iloc[-1] < end:
                next_start = data[-1]["Timestamp"].iloc[-1] + datetime.timedelta(minutes=int(interval))
                next_end = next_start + datetime.timedelta(minutes=int(interval)*limit)
                data.append(self.get_data_helper(next_start, next_end, symbol, interval, limit))
        except:
            pass
            
        data = pd.concat(data, axis=0)
        data.reset_index(inplace=True, drop=True)
        data = data.loc[data["Timestamp"] <= end]
        self.logger.info(f"{len(data)} data points retrieved for {symbol} from {start} to {end}.")
        return data
    