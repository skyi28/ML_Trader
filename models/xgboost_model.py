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
        path_to_config += f'\config'
        break

import pandas as pd
import xgboost as xgb
from config.config import load_config
from infrastructure.database import Database
from infrastructure.logger import create_logger

class XGBoostModel:
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
        if mode == 'direction':
            model = xgb.XGBClassifier()
        if mode == 'return':
            model = xgb.XGBRegressor()
        
        if params is None:
            params = self.get_default_params(mode)
        
        model.set_params(**params)
        return model
    
    def train(self, model, features: pd.DataFrame, target: pd.Series):
        #d_matrix = xgb.DMatrix(features, target, enable_categorical=True)
        model.fit(features, target)
        return model
    
    def predict(self, model, features: pd.DataFrame):
        return model.predict(features)
        