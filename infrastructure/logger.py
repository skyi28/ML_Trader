"""
This python module contains a function to create and configure a logger.
"""
import os
import sys
basedir = os.path.abspath(os.path.dirname(__file__)) + os.sep
basedir_split = basedir.split(os.sep)
path_to_config = ''
for part in basedir_split:
    path_to_config += part + os.sep
    if part == "ML_Trader":
        path_to_config += f'config'
        break
sys.path.append(path_to_config)

import logging
from logging.handlers import TimedRotatingFileHandler
from config.config import load_config

config = load_config(f'{path_to_config}{os.sep}config.yaml')

def create_logger(log_file: str, log_dir: str = 'logs') -> logging.Logger:
    """
    Creates and configures a logger instance with a TimedRotatingFileHandler.

    Parameters:
    - log_file (str): The name of the log file.
    - log_dir (str): The directory where the log file will be stored. Default is 'logs'.

    Returns:
    - logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(log_file)
    if config.logging.log_level == 'DEBUG':
        level = logging.DEBUG
    elif config.logging.log_level == 'INFO':
        level = logging.INFO
    elif config.logging.log_level == 'WARNING':
        level = logging.WARNING
    elif config.logging.log_level == 'ERROR':
        level = logging.ERROR
    elif config.logging.log_level == 'CRITICAL':
        level = logging.CRITICAL
    else:
        level = logging.INFO    
    logger.setLevel(level)
    
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler = TimedRotatingFileHandler(filename=f'{log_dir}/{log_file}', when='midnight', backupCount=8)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
