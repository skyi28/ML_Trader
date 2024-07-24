"""
This python module contains a function to load the configurations from the config.yaml file
and parses its content to a munch object which can be accessed using Python syntax.
"""
import pathlib
import munch
import yaml

PROJECT_ROOT: str = str(pathlib.Path(__file__).parent.resolve())

def load_config(config_file_path: str) -> munch.Munch:
    """
    Load and parse a YAML configuration file, replacing any occurrences of '<<project_root>>' 
    with the absolute path of the project root.

    Parameters:
    - config_file_path (str): The path to the YAML configuration file.

    Returns:
    - munch.Munch: A munchified dictionary containing the parsed configuration data.
    """
    with open(config_file_path, 'r', encoding='UTF-8') as file:
        yaml_str: str = file.read()        
        yaml_str = yaml_str.replace('<<project_root>>', PROJECT_ROOT)
        config_data: dict = yaml.safe_load(yaml_str)
        return munch.munchify(config_data)
