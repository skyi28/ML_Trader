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
    
import pickle
import numpy as np
from sklearn.metrics import confusion_matrix, balanced_accuracy_score, accuracy_score, precision_score, recall_score
    
from config.config import load_config
from infrastructure.database import Database

class ModelBase():
    """
    Base class for all model-related operations. Contains several functions which are necessary for all models.
    """
    def __init__(self, db, config) -> None:
        """
        Initializes a new instance of the ModelBase class.

        This constructor takes two parameters: a Database object (db) and a Config object (config).
        The Database object provides methods for interacting with the database, while the Config object
        contains configuration settings for the application.

        Parameters:
        - db (Database): An instance of the Database class, which provides methods for interacting with the database.
        - config (Config): An instance of the Config class, which contains configuration settings for the application.

        Returns:
        - None: The constructor does not return any value. It initializes the ModelBase instance with the provided db and config objects.
        """
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
        technical_indicators = [f'"{technical_indicator}"' for technical_indicator in technical_indicators]
        
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

    def save_model(self, model, user: int, model_id: int) -> None:
        """
        Saves a trained model to a specified location in the filesystem.

        The function constructs the path to the model file based on the user and model ID,
        then uses the pickle module to serialize the model and save it to the filesystem.

        Parameters:
        - model: The trained model object to be saved.
        - user (int): The unique identifier of the user who owns the model.
        - model_id (int): The unique identifier of the model.

        Returns:
        - None: The function does not return any value.
        """
        path_to_model: str = self.config.path_to_models.replace(f'{os.sep}config','')
        pickle.dump(model, open(f'{path_to_model}model_{user}_{model_id}.pkl', 'wb'))


    def load_model(self, user: int, model_id: int) -> object:
        """
        Loads a trained model from the filesystem based on the provided user and model ID.

        The function constructs the path to the model file based on the user and model ID,
        then uses the pickle module to deserialize the model and return it.

        Parameters:
        - user (int): The unique identifier of the user who owns the model.
        - model_id (int): The unique identifier of the model.

        Returns:
        - object: The loaded trained model object.
        """
        path_to_model: str = self.config.path_to_models.replace(f'{os.sep}config','')
        model = pickle.load(open(f'{path_to_model}model_{user}_{model_id}.pkl', 'rb'))
        return model


    def create_confusion_matrix(self, y_test: np.array, y_pred: np.array) -> np.array:
        """
        Creates a confusion matrix to evaluate the performance of a classification model.

        Parameters:
        - y_test (np.array): The true labels of the test dataset.
        - y_pred (np.array): The predicted labels of the test dataset.

        Returns:
        - np.array: A 2D array representing the confusion matrix. The rows represent the true labels,
        and the columns represent the predicted labels.
        """
        return confusion_matrix(y_test, y_pred)


    def calc_accuracy(self, y_test: np.array, y_pred: np.array) -> float:
        """
        Calculates the accuracy of a classification model.

        The accuracy is defined as the ratio of correctly predicted samples to the total number of samples.
        It is a common evaluation metric for classification problems.

        Parameters:
        - y_test (np.array): A 1D numpy array containing the true labels of the test dataset.
        - y_pred (np.array): A 1D numpy array containing the predicted labels of the test dataset.

        Returns:
        - float: The accuracy score, a value between 0 and 1, where 1 indicates perfect accuracy.
        """
        return accuracy_score(y_test, y_pred)


    def calc_balanced_accuracy(self, y_test: np.array, y_pred: np.array) -> float:
        """
        Calculates the balanced accuracy of a classification model.

        Balanced accuracy is a metric that calculates the average of recall obtained on each class.
        It is a more robust metric for imbalanced datasets compared to simple accuracy.

        Parameters:
        - y_test (np.array): A 1D numpy array containing the true labels of the test dataset.
        - y_pred (np.array): A 1D numpy array containing the predicted labels of the test dataset.

        Returns:
        - float: The balanced accuracy score, a value between 0 and 1, where 1 indicates perfect balanced accuracy.
        """
        return balanced_accuracy_score(y_test, y_pred)


    def calc_precision(self, y_test: np.array, y_pred: np.array) -> float:
        """
        Calculates the precision score of a classification model.

        Precision is a metric that measures the proportion of correctly predicted positive instances out of all predicted positive instances.
        It is a useful metric for evaluating the performance of a classification model, especially in cases where false positives are more costly.

        Parameters:
        - y_test (np.array): A 1D numpy array containing the true labels of the test dataset.
        - y_pred (np.array): A 1D numpy array containing the predicted labels of the test dataset.

        Returns:
        - float: The precision score, a value between 0 and 1, where 1 indicates perfect precision.
        """
        return precision_score(y_test, y_pred)


    def calc_recall(self, y_test: np.array, y_pred: np.array) -> float:
        """
        Calculates the recall score of a classification model.

        Recall is a metric that measures the proportion of correctly predicted positive instances out of all actual positive instances.
        It is a useful metric for evaluating the performance of a classification model, especially in cases where false negatives are more costly.

        Parameters:
        - y_test (np.array): A 1D numpy array containing the true labels of the test dataset.
        - y_pred (np.array): A 1D numpy array containing the predicted labels of the test dataset.

        Returns:
        - float: The recall score, a value between 0 and 1, where 1 indicates perfect recall.
        """
        return recall_score(y_test, y_pred)
