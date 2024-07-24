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

import pandas as pd
import numpy as np
from config import load_config

class TechnicalIndicators:
    def __init__(self) -> None:
        self.config = load_config(f'{path_to_config}{os.sep}config.yaml')
    
    def calc_moving_average(self, data: pd.Series, window_size: int = None):
        """
        Calculates the moving average of a time series.

        Parameters
        ----------
        data : pd.Series
            The time series data.
        window_size : int
            The size of the moving average window.


        Returns
        -------
        pd.Series
            The moving average values.

        """
        if not window_size:
            window_size = self.config.technical_indicators.moving_average.period
        return data.rolling(window=window_size).mean()
    
    def calc_exponential_moving_average(self, data: pd.Series, window_size: int = None) -> pd.Series:
        """
        Calculates the Exponential Moving Average (EMA) of a time series.

        Parameters
        ----------
        data : pd.Series
            The time series data.
        window_size : int
            The size of the EMA window.

        Returns
        -------
        pd.Series
            The EMA values.

        """
        if not window_size:
            window_size = self.config.technical_indicators.exponential_moving_average.period
        result = data.ewm(span=window_size).mean()
        result.iloc[0:window_size - 1] = np.nan
        return result
    
    def calc_moving_std(self, data: pd.Series, window_size: int = None) -> pd.Series:
        """
        Calculates the moving standard deviation of a time series.

        Parameters
        ----------
        data : pd.Series
            The time series data.
        window_size : int
            The size of the moving average window.

        Returns
        -------
        pd.Series
            The moving standard deviation values.

        """
        if not window_size:
            window_size = self.config.technical_indicators.moving_std.period
        return data.rolling(window=window_size).std()
    
    def calc_macd(self, data: pd.Series, shorter: int = None, longer: int = None) -> pd.Series:
        """
        Calculates the MACD (Moving Average Convergence/Divergence) of a time series.

        Parameters
        ----------
        data : pd.Series
            The time series data.
        shorter : int, optional
            The shorter moving average window size. The default is 12.
        longer : int, optional
            The longer moving average window size. The default is 26.

        Returns
        -------
        pd.Series
            The MACD values.

        """
        if not shorter:
            shorter = self.config.technical_indicators.macd.shorter
        if not longer:
            longer = self.config.technical_indicators.macd.longer
        macd = self.calc_moving_average(data, shorter) - self.calc_moving_average(data, longer)
        return macd
    
    def calc_rsi(self, data: pd.Series, window_size: int = None) -> pd.Series:
        """
        Calculates the relative strength index (RSI) of a time series.

        Parameters
        ----------
        data : pd.Series
            The time series data.
        period : int, optional
            The RSI period. The default is 14.

        Returns
        -------
        pd.Series
            The RSI values.

        """
        if not window_size:
            window_size = self.config.technical_indicators.rsi.period
        price_diff = data.diff()
        gains = price_diff.where(price_diff > 0, 0)
        losses = -price_diff.where(price_diff < 0, 0)
        avg_gains = gains.rolling(window=window_size, min_periods=1).mean()
        avg_losses = losses.rolling(window=window_size, min_periods=1).mean()
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        rsi.iloc[0:window_size - 1] = np.nan
        return rsi
    
    def calc_momentum(self, data: pd.Series, window_size: int = None) -> pd.Series:
        """
        Calculates the momentum of a time series.

        Parameters
        ----------
        data : pd.Series
            The time series data.
        window_size : int, optional
            The size of the moving average window. The default is 10.

        Returns
        -------
        pd.Series
            The momentum values.

        """
        if not window_size:
            window_size = self.config.technical_indicators.momentum.period
        price_shifted = data.shift(window_size)
        momentum = data - price_shifted
        return momentum 
    
    def calc_periodic_highs(self, data: pd.Series, window_size: int = None) -> pd.Series:
        """
        Calculates the highest value over a specific period of time.

        Parameters
        ----------
        data : pd.Series
            The data frame containing the time series data.
        window_size : int, optional
            The size of the moving average window. The default is 10.

        Returns
        -------
        pd.Series
            The highest value over the specified period.

        """
        if not window_size:
            window_size = self.config.technical_indicators.periodic_highs.period
        periodic_highs = data.rolling(window_size).max()
        return periodic_highs
    
    def calc_periodic_lows(self, data: pd.Series, window_size: int = None) -> pd.Series:
        """
        Calculates the lowest value over a specific period of time.

        Parameters
        ----------
        data : pd.Series
            The data frame containing the time series data.
        window_size : int, optional
            The size of the moving average window. The default is 10.

        Returns
        -------
        pd.Series
            The lowest value over the specified period.

        """
        if not window_size:
            window_size = self.config.technical_indicators.periodic_lows.period
        periodic_lows = data.rolling(window_size).min()
        return periodic_lows
    
    def calc_bollinger_bands(self, data: pd.Series, window_size: int = None, std_dev: int = None) -> tuple:
        """
        Calculates the Bollinger Bands for a given time series.

        Bollinger Bands are a technical indicator used to identify overbought and oversold conditions.
        They consist of three lines: a simple moving average (middle band), an upper band, and a lower band.
        The upper and lower bands are typically set at a certain number of standard deviations above and below the middle band.

        Parameters:
        ----------
        data : pd.Series
            The time series data.
        window_size : int, optional
            The size of the moving average window. If not provided, it will be fetched from the configuration.
        std_dev : int, optional
            The number of standard deviations for the upper and lower bands. If not provided, it will be fetched from the configuration.

        Returns:
        -------
        pd.Series, pd.Series
            The lower band and upper band values.
        """
        if not window_size:
            window_size = self.config.technical_indicators.bollinger_bands.period
        if not std_dev:
            std_dev = self.config.technical_indicators.bollinger_bands.std_dev
            
        middle: pd.Series = data.rolling(window_size).mean()
        std: pd.Series = data.rolling(window_size).std()
        
        return middle - (std_dev * std), middle + (std_dev * std)
