# author : Gabriel Santini Francisco
# email  : gabrielsantinifrancisco@outlook.com

# Description:
# This module defines a CustomLogger class for structured and configurable logging.
# It supports logging to both file and console, allows dynamic configuration of log levels and formats,
# and provides methods for logging messages at various severity levels with contextual information.
# The logger is intended for use in applications requiring flexible and detailed logging capabilities.

import logging, sys, inspect

class CustomLogger:
    """
    A custom logging class that provides structured logging capabilities.

    This class handles different log levels, console output, and integrates with the
    application's configuration system to provide flexible logging options.
    """
    
    def __init__(self, config: dict, logger_name: str = "CustomLogger"):
        """
        Initialize the logger with configuration settings.
        
        Args:
            config (dict): Logging configuration dictionary containing settings like level, file paths, etc.
            logger_name (str): Name for the logger instance. Defaults to "CustomLogger".
        """
        self.config = config
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(getattr(logging, config.get('level', 'INFO').upper()))
        
        # Clear any existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        if config.get('enabled', True): self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up file and console handlers based on configuration."""
        formatter = logging.Formatter(
            self.config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            datefmt=self.config.get('date_format', '%Y-%m-%d %H:%M:%S')
        )
        
        if self.config.get('log_to_file', True):
            try:
                file_handler = logging.FileHandler(
                    self.config.get('log_file_path', './token_manager.log')
                )
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                print(f"Warning: Could not set up file logging: {e}")
        
        if self.config.get('log_to_console', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def debug(self, message: str, **kwargs):    self.logger.debug(self._format_message(message, **kwargs))
    def info(self, message: str, **kwargs):     self.logger.info(self._format_message(message, **kwargs))
    def warning(self, message: str, **kwargs):  self.logger.warning(self._format_message(message, **kwargs))
    def error(self, message: str, **kwargs):    self.logger.error(self._format_message(message, **kwargs))
    def critical(self, message: str, **kwargs): self.logger.critical(self._format_message(message, **kwargs))

    def _format_message(self, message: str, **kwargs) -> str:
        """Format the message with additional context, module, and function name."""
        stack = inspect.stack()

        module = inspect.getmodule(stack[2][0])
        module_name = module.__name__.split('.')[-1] if module else "UNKNOWN"
        function_name = stack[2][3]
        if function_name == "<module>":
            function_name = "MAIN"

        module_name = module_name.split('/')[-1].replace('.py', '').capitalize()
        if kwargs:
            context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            return f"[{module_name}:{function_name}] - {message} | {context}"
        return f"[{module_name}:{function_name}] - {message}"