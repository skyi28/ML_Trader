"""
This python module contains functions which are needed for all models.
"""
import os
basedir = os.path.abspath(os.path.dirname(__file__)) + os.sep
basedir_split = basedir.split(os.sep)
path_to_config = ''
for part in basedir_split:
    path_to_config += part + os.sep
    if part == "ML_Trader":
        path_to_config += f'\config'
        break
    
from config.config import load_config
from infrastructure.database import Database

class ModelBase():
    def __init__(self, db, config) -> None:
        self.db = db
        self.config = config
    
    def get_model_params_from_database(self, user: int, model_id: int) -> dict:
        query: str = f'SELECT * FROM models WHERE "user"={user} AND id={model_id}'
        model_data = self.db.execute_read_query(query, return_type='pd.DataFrame')
        hyper_parameters = model_data['hyper_parameters'].iloc[0]
        return hyper_parameters
    
    def get_technical_indicators_from_database(self, user: int, model_id: int) -> list[str]:
        query: str = f'SELECT * FROM models WHERE "user"={user} AND id={model_id}'
        model_data = self.db.execute_read_query(query, return_type='pd.DataFrame')
        technical_indicators = model_data['technical_indicators'].iloc[0].split(',')
        return technical_indicators
