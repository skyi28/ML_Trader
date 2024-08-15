"""
This python module contains functions needed to let all running models make predictions.
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
import threading
    
from config.config import load_config
from infrastructure.database import Database
from models.prepare_training_data import PrepareTrainingData
from models.xgboost_model import XGBoostModel

class ExecuteModels:
    def __init__(self) -> None:
        self.config = load_config(f'{path_to_config}{os.sep}config.yaml')
        self.db = Database()
        self.ptd = PrepareTrainingData()
        
    def prediction_loop(self) -> None:
        while True:
            if datetime.datetime.now().second == 0:
                time.sleep(0.5) # TODO This makes sure that the data is available in the database. Write code which checks if the data is available and then execute the following code
                running_models = self.db.get_all_running_models()
                for _, row in running_models.iterrows():
                    prediction_features: pd.DataFrame = self.ptd.load_data_for_prediction(
                        symbol=row['symbol'],
                        feature_columns=row['technical_indicators'].split(',')
                    )
                    if row['model_type'].lower() == 'xgboost':
                        xgb_class = XGBoostModel()
                        model = xgb_class.load_model(row['user'], row['id'])
                    print(f'Model_{row["user"]}_{row["id"]} predicts for {row["symbol"]}: ', model.predict(prediction_features))
                    