# author : Gabriel Santini Francisco
# email  : gabrielsantinifrancisco@outlook.com


# Description:
# CustomLogger provides structured, configurable logging with transaction ID support.
# Features:
# - Logging to file and/or console
# - Dynamic log level and format configuration
# - Methods for all standard log levels
# - Contextual info: module and function names
# - Transaction ID tracking for end-to-end traceability
# Suitable for applications needing flexible, detailed logging.

##########################
# INITIAL SETUP
##########################

import logging, os, sys, inspect, string, secrets, traceback

class FailInitLogging(Exception): pass

class TransactionIDFilter(logging.Filter):
    """A logging filter that adds a transaction ID to each log record."""
    def __init__(self, transaction_id):
        super().__init__()
        self.transaction_id = transaction_id

    def filter(self, record):
        record.transaction_id = self.transaction_id
        return True

class CustomLogger:
    """
    A custom logging class that provides structured logging capabilities with transaction ID support.

    This class handles different log levels, console output, transaction ID tracking, and integrates with the
    application's configuration system to provide flexible logging options.
    """

    def __init__(self, config: dict, logger_name: str = "CustomLogger", transaction_id: str = None):
        """
        Initialize the logger with configuration settings and optional transaction ID.
        
        Args:
            config (dict): Logging configuration dictionary containing settings like level, file paths, etc.
            logger_name (str): Name for the logger instance. Defaults to "CustomLogger".
            transaction_id (str): Optional transaction ID for tracking related operations. Defaults to None.
        """
        self.config = config
        self.transaction_id = transaction_id or 'NoTransactionID'
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(getattr(logging, config.get('level', 'INFO').upper()))
        self.logger.handlers.clear()
        self.logger.addFilter(TransactionIDFilter(self.transaction_id))

        if config['enabled'] and (config['log_to_file'] or config['log_to_console']):
            self._setup_handlers()
        else:
            raise FailInitLogging(f"""
Failed to initialize logging
At least one of the following must be enabled in the logging configuration:
- log_to_file
- log_to_console
""")

    def _setup_handlers(self):
        """Set up file and console handlers based on configuration with transaction ID support."""
        base_format = self.config.get('format', '%(asctime)s - [ {transaction_id} ] - %(name)s - %(levelname)s - %(message)s')
        formatter = logging.Formatter(
            base_format,
            datefmt=self.config.get('date_format', '%Y-%m-%d %H:%M:%S')
        )

        if self.config.get('log_to_file', True):
            os.makedirs(os.path.dirname(self.config['log_file_path']), exist_ok=True)
            try:
                file_handler = logging.FileHandler(
                    self.config['log_file_path']
                )
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                print(f"Warning: Could not set up file logging: {e}")
                print(f'\n{traceback.format_exc()}')
                raise

        if self.config.get('log_to_console', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def generate_transaction_id(self) -> str:
        """Generate a 12-character random transaction ID using a-z A-Z 0-9."""
        alphabet = string.ascii_letters + string.digits 
        return ''.join(secrets.choice(alphabet) for _ in range(12))
    
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
        if function_name == "<module>": function_name = "MAIN"

        module_name = module_name.split('/')[-1].replace('.py', '').capitalize()
        if kwargs:
            context = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            return f"[{module_name}:{function_name}] - {message} | {context}"
        return f"[{module_name}:{function_name}] - {message}"