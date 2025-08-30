# Author : Gabriel Santini Francisco
# Email  : gabrielsantinifrancisco@outlook.com

# Description:
#     This script provides utility functions for cleaning and processing historical JSON data. 
#     It includes functionality to read configuration files, set up environment variables and logging, 
#     filter JSON data to retain only specified fields, and save the processed data to disk. 
#     The script is designed to be configurable and extensible, supporting custom logging and flexible field selection.

class EnvManager:
    """
    EnvManager is a utility class for loading configuration from a Python file and setting environment variables accordingly.

    Attributes:
        config (dict): The configuration dictionary loaded from the specified file.

    Methods:
        __init__(config_path: str):
            Initializes the EnvManager by loading the configuration from the given file path and setting environment variables.

        read_config(file_path: str) -> dict:
            Reads a Python configuration file and returns its variables as a dictionary.

        set_env(config: dict) -> None:
            Sets environment variables and instance attributes based on the provided configuration dictionary.
    """
    def __init__(self, config_path: str):
        """Initialize EnvManager by loading config and setting environment variables."""
        self.config = self.read_config(config_path)
        self.set_env(self.config)

    @staticmethod
    def read_config(file_path: str) -> dict:
        """Read a Python config file and return its variables as a dict."""
        with open(file_path, 'r') as file: config_content = file.read()
        config = {}
        exec(config_content, config)
        config.pop('__builtins__', None)
        return config

    def set_env(self, config: dict) -> None:
        """Set environment variables and initialize logger from config."""
        for key, value in config.items():
            setattr(self, key, value)
            globals()[key] = value  