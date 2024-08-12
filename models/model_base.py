"""
This python module contains functions which are needed for all bots.
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
    
from config.config import load_config
from infrastructure.database import Database

class ModelBase():
    def __init__(self, db, config) -> None:
        self.db = db
        self.config = config
    
    def get_model_params_from_database(self, user: int, model_id: int) -> dict:
        """
        Retrieves the hyperparameters of a specific model from the database.

        Parameters:
        user (int): The unique identifier of the user who owns the model.
        model_id (int): The unique identifier of the model.

        Returns:
        dict: A dictionary containing the hyperparameters of the model.
        """
        query: str = f'SELECT * FROM bots WHERE "user"={user} AND id={model_id}'
        model_data = self.db.execute_read_query(query, return_type='pd.DataFrame')
        hyper_parameters = model_data['hyper_parameters'].iloc[0]
        return hyper_parameters
    
    def get_technical_indicators_from_database(self, user: int, model_id: int) -> list[str]:
        """
        Retrieves the technical indicators associated with a specific model from the database.

        Parameters:
        user (int): The unique identifier of the user who owns the model.
        model_id (int): The unique identifier of the model.

        Returns:
        list[str]: A list of strings representing the technical indicators associated with the model.
        """
        query: str = f'SELECT * FROM bots WHERE "user"={user} AND id={model_id}'
        model_data = self.db.execute_read_query(query, return_type='pd.DataFrame')
        technical_indicators = model_data['technical_indicators'].iloc[0].split(',')
        return technical_indicators
    
    def get_symbol_from_database(self, user: int, model_id: int) -> str:
        """
        Retrieves the symbol associated with a specific model from the database.

        Parameters:
        user (int): The unique identifier of the user who owns the model.
        model_id (int): The unique identifier of the model.

        Returns:
        str: The symbol associated with the model, converted to lowercase.
        """
        query: str = f'SELECT symbol FROM bots WHERE "user"={user} AND id={model_id}'
        symbol = self.db.execute_read_query(query, return_type='pd.DataFrame')
        symbol = symbol['symbol'].iloc[0]
        return symbol.lower()