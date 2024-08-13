"""
This python module contains functions create, train and predict utilizing a xgboost model.
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

import pandas as pd
import datetime
import xgboost as xgb
import pickle

from config.config import load_config

from infrastructure.logger import create_logger
from infrastructure.database import Database

from models.model_base import ModelBase
from models.prepare_training_data import PrepareTrainingData

class XGBoostModel(ModelBase):
    def __init__(self, id: int) -> None:
        """
        Initialize the XGBoostModel class with the provided id.

        Parameters:
        - id (int): The unique identifier for the model instance.

        Returns:
        - None: The __init__ method does not return anything. It initializes the class attributes.
        """
        self.db = Database()
        self.config = load_config(f'{path_to_config}{os.sep}config.yaml')
        self.logger = create_logger('xgboost.log')
        self.ptd = PrepareTrainingData()
        super().__init__(self.db, self.config)
        
    def get_default_params(self, mode: str = 'direction') -> dict:
        """
        This function returns the default parameters for the XGBoost model based on the specified mode.

        Parameters:
        - mode (str): The mode for which the default parameters are required. It can be either 'direction' or 'return'.
            Default value is 'direction'.

        Returns:
        - dict: A dictionary containing the default parameters for the XGBoost model.
        """
        if mode == 'direction':
            default_params = {
                'n_estimators': 1500,
                'max_depth': 5,
                'learning_rate': 0.05,
                'gamma': 2,
                'colsample_bytree': 0.8,
                'objective': 'binary:logistic',
            }
        elif mode == 'return':
            default_params = {
                'n_estimators': 1500,
                'max_depth': 5,
                'learning_rate': 0.05,
                'gamma': 2,
                'colsample_bytree': 0.8,
                'objective':'reg:squarederror',
            }
        return default_params
        
    def create_model(self, mode: str = 'direction', params: dict = None) -> xgb.XGBClassifier | xgb.XGBRegressor:
        """
        This function creates an XGBoost model based on the specified mode and parameters.

        Parameters:
        - mode (str): The mode for which the model is created. It can be either 'direction' or 'return'.
                    Default value is 'direction'.
        - params (dict): A dictionary containing the parameters for the XGBoost model. If None, the default parameters
                        will be used based on the specified mode.

        Returns:
        - xgb.XGBClassifier | xgb.XGBRegressor based on the specified mode.
        """
        # TODO Error handling
        if mode == 'direction':
            model = xgb.XGBClassifier()
        if mode == 'return':
            model = xgb.XGBRegressor()
        
        if params is None:
            params = self.get_default_params(mode)
        
        model.set_params(**params)
        return model
    
    # TODO Function to create model from the database
    
    def train(self, user: int, model_id: int, model: xgb.XGBClassifier, start_date: datetime.datetime, end_date: datetime.datetime, train_size: float) -> None:
        """
        Trains the XGBoost model using data from the specified symbol and technical indicators within the given date range.

        Parameters:
        - user (int): The unique identifier of the user for whom the model is being trained.
        - model_id (int): The unique identifier of the model instance.
        - model (xgb.XGBClassifier): The model instance which should be trained.
        - start_date (datetime.datetime): The start date of the data range for training.
        - end_date (datetime.datetime): The end date of the data range for training.
        - train_size (float): The proportion of the data to be used for training (between 0 and 1).

        Returns:
        - None: The function does not return anything. It trains the XGBoost model using the specified data.
        """
        symbol: str = self.get_symbol_from_database(user, model_id)
        technical_indicators: list[str] = self.get_technical_indicators_from_database(user, model_id)
        
        data = self.ptd.load_data(symbol, feature_columns=technical_indicators, min_date=start_date, max_date=end_date)
        data = data.pipe(self.ptd.remove_na).pipe(self.ptd.remove_timestamp).pipe(self.ptd.add_return).pipe(self.ptd.add_direction, remove_zeros=True)
        features, target = self.ptd.create_features_and_targets(data)        
                
        model.fit(features, target)
        
        self.save_model(model, user, model_id)
    
    def train_old(self, model, features: pd.DataFrame, target: pd.Series):
        # TODO Error handling
        model.fit(features, target)
        return model
    
    def predict(self, model, features: pd.DataFrame):
        # TODO Error handling
        return model.predict(features)
        
    # TODO Function for calculating error metrics
