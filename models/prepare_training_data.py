"""
This python module contains functions prepare data for the training of several model types.
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

import pandas as pd
import numpy as np

from infrastructure.database import Database
from infrastructure.logger import create_logger

class PrepareTrainingData:
    def __init__(self) -> None:
        """
        Initialize PrepareTrainingData class.

        This function initializes the PrepareTrainingData class by creating instances of the Database and Logger classes.
        The Database instance is used to interact with the database, while the Logger instance is used for logging purposes.

        Parameters:
        - None

        Returns:
        - None
        """
        self.db = Database()
        self.logger = create_logger('prepare_training_data.log')
        
    def load_data_for_prediction(self, symbol, feature_columns: list[str]) -> pd.DataFrame:
        """
        Load the latest data for a specific symbol from the database for prediction purposes.

        This function constructs a SQL query to retrieve the latest data for a given symbol from the database.
        If 'open' or 'close' columns are not specified in the feature_columns list, they are added at the beginning.
        The function assumes that the historic price data is inserted in ascending order by time.

        Parameters:
        - symbol (str): The symbol for which data needs to be retrieved.
        - feature_columns (list[str]): A list of column names to select. If 'open' or 'close' are not included, they are added at the beginning.

        Returns:
        - pd.DataFrame: A pandas DataFrame containing the latest data for the specified symbol.
        """
        if 'open' not in feature_columns:
            feature_columns.insert(0, 'open')
        if 'close' not in feature_columns:
            feature_columns.insert(1,'close')
        for idx, feature in enumerate(feature_columns):
            if feature.find(' ') != -1:
                feature_columns[idx] = feature.replace(' ','_')

        # This assumes that the historic price data is inserted ascending by time
        query = f"SELECT {','.join(feature_columns)} FROM {symbol} ORDER BY timestamp DESC LIMIT(1)"
        data: pd.DataFrame = self.db.execute_read_query(query, return_type='pd.DataFrame')
        data = self.add_return(data)
        data = self.remove_na(data)
        return data

        
    def load_data(self, symbol: str, feature_columns: list[str] = None, min_date: str = None, max_date: str = None) -> pd.DataFrame:
        """
        Load data from the database for a specific symbol.

        This function constructs a SQL query based on the provided parameters and executes it to retrieve data from the database.
        If no feature columns are specified, all columns are selected.
        The function also allows filtering data based on minimum and maximum dates.

        Parameters:
        - symbol (str): The symbol for which data needs to be retrieved.
        - feature_columns (list[str], optional): A list of column names to select. If not provided, all columns are selected. Defaults to None.
        - min_date (str, optional): The minimum date for filtering data. If provided, only data with a timestamp greater than or equal to this value is returned. Defaults to None.
        - max_date (str, optional): The maximum date for filtering data. If provided, only data with a timestamp less than or equal to this value is returned. Defaults to None.

        Returns:
        - pd.DataFrame: A pandas DataFrame containing the retrieved data.
        """
        if not feature_columns:
            query: str = f"SELECT * FROM {symbol}"
        else:
            if 'open' not in feature_columns:
                feature_columns.insert(0, 'open')
            if 'close' not in feature_columns:
                feature_columns.insert(1,'close')
            for idx, feature in enumerate(feature_columns):
                if feature.find(' ') != -1:
                    feature_columns[idx] = feature.replace(' ','_')
            query: str = f"SELECT {','.join(feature_columns)} FROM {symbol}"
            
        if min_date:
            query += f" WHERE TO_TIMESTAMP('{min_date}', 'YYYY-MM-DD HH24:MI') <= timestamp"
        if max_date:
            if min_date:
                query += " AND"
            else:
                query += " WHERE"
            query += f" TO_TIMESTAMP('{max_date}', 'YYYY-MM-DD HH24:MI') >= timestamp"
            
        return self.db.execute_read_query(query, return_type='pd.DataFrame')
    
    def remove_na(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Remove rows with missing values (NaN) from the input DataFrame.

        This function takes a pandas DataFrame as input and removes any rows that contain missing values (NaN).
        The function modifies the input DataFrame in-place and returns the modified DataFrame.

        Parameters:
        - data (pd.DataFrame): The input DataFrame from which to remove rows with missing values.

        Returns:
        - pd.DataFrame: The modified DataFrame with rows containing missing values removed.
        """
        data.dropna(inplace=True)
        return data
    
    def remove_timestamp(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Remove the 'timestamp' column from the input DataFrame.

        This function takes a pandas DataFrame as input and removes the 'timestamp' column.
        The function modifies the input DataFrame in-place and returns the modified DataFrame.

        Parameters:
        - data (pd.DataFrame): The input DataFrame from which to remove the 'timestamp' column.
            The DataFrame should contain a 'timestamp' column.

        Returns:
        - pd.DataFrame: The modified DataFrame with the 'timestamp' column removed.
        """
        try:
            data = data.drop(columns=['timestamp'])
        except Exception as e:
            self.logger.error(f'Error removing timestamp column: {str(e)}')
        return data
        
    def add_return(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Adds a new column 'return' to the input DataFrame, which represents the daily return of the 'close' price relative to the 'open' price.

        Parameters:
        - data (pd.DataFrame): The input DataFrame containing 'close' and 'open' price columns.
            The DataFrame should have at least these two columns.

        Returns:
        - pd.DataFrame: The modified DataFrame with an additional 'return' column.
            The 'return' column contains the daily return values calculated as (close - open) / close.
        """
        try:
            data['return'] = (data['close'] - data['open']) / data['close']
        except Exception as e:
            self.logger.error(f'Error adding return column: {str(e)}')
        return data
    
    def add_direction(self, data: pd.DataFrame, remove_zeros: bool=True) -> pd.DataFrame:
        """
        Adds a new column 'direction' to the input DataFrame, which represents the direction of the 'return' values.

        Parameters:
        - data (pd.DataFrame): The input DataFrame containing 'return' column.
            The DataFrame should have at least a 'return' column.

        - remove_zeros (bool, optional): A flag indicating whether to remove rows with zero direction.
            If True, rows with zero direction are removed from the DataFrame.
            Defaults to True.

        Returns:
        - pd.DataFrame: The modified DataFrame with an additional 'direction' column.
            The 'direction' column contains binary values representing the direction of the 'return' values.
            -1 is replaced with 0.
        """
        if 'return' not in data.columns:
            self.logger.error('Can not add direction because return column is missing. Returning data without direction')
            return data
        
        data['direction'] = np.sign(data['return'])
        if remove_zeros:
            data = data[data['direction'] != 0]
        
        data['direction'] = data['direction'].astype(int)
        data['direction'] = data['direction'].replace(-1, 0)
        return data
    
    # TODO add first difference method as step in data pipeline
    
    def create_features_and_targets(self, data: pd.DataFrame, target_column: str = 'direction') -> tuple:
        """
        This function separates the input DataFrame into features and target variables.

        Parameters:
        - data (pd.DataFrame): The input DataFrame containing both features and target variables.
            The DataFrame should have at least one column for the target variable.

        - target_column (str, optional): The name of the column to be used as the target variable.
            Defaults to 'direction'.

        Returns:
        - tuple: A tuple containing one pandas data frame (features) and one pandas Series (target):
            - features: A pandas data frame containing all columns from the input DataFrame except the target column.
            - target: A pandas series containing the target column.
        """
        features = data.loc[:, data.columns != target_column]
        target = data.loc[:, target_column]
        return features, target
    
    def create_training_and_testing_set(self, features: pd.DataFrame, target: pd.Series, train_size: float) -> tuple:
        """
        This function splits the input features and target data into training and testing sets based on the specified train_size.

        Parameters:
        - features (pd.DataFrame): A pandas DataFrame containing the features for the machine learning model.
        - target (pd.Series): A pandas Series containing the target variable for the machine learning model.
        - train_size (float): A float value between 0 and 1 representing the proportion of the data to include in the training set.

        Returns:
        - tuple: A tuple containing four elements:
            - train_features (pd.DataFrame): The training set of features.
            - train_target (pd.Series): The training set of target values.
            - test_features (pd.DataFrame): The testing set of features.
            - test_target (pd.Series): The testing set of target values.
        If train_size is 1, the function returns the entire features and target data as the training set, and None for the testing set.
        """
        if train_size == 1:
            return features, target, None, None

        split_index: int = int(len(features) * train_size)

        train_features: pd.DataFrame = features.loc[:split_index, :]
        train_target: pd.Series = target.loc[:split_index]

        test_features: pd.DataFrame = features.loc[split_index:, :]
        test_target: pd.Series = target.loc[split_index:]

        return train_features, train_target, test_features, test_target

    
    # TODO Data preperation for other models