# author : Gabriel Santini Francisco
# email  : gabrielsantinifrancisco@outlook.com

# Description: 
# Retrieves the WebSocket link and Sec-WebSocket-Key for a given Race Monitor race ID
# by launching a headless Chrome browser, navigating to the Race Monitor API page,
# capturing browser performance logs, and extracting the relevant WebSocket connection
# information from the network requests. Useful for automating access to real-time
# race data streams that require dynamic WebSocket authentication.

from CustomLogger import CustomLogger
from EnvManager import EnvManager
import json, inspect, traceback

class RaceMonitorKeyRetriever:
    """
    RaceMonitorKeyRetriever is a utility class for retrieving the WebSocket link and Sec-WebSocket-Key
    required to connect to a Race Monitor timing session.
    This class initializes environment and logging configurations, and provides a method to automate
    the extraction of WebSocket connection details from the Race Monitor API using a headless Selenium
    Chrome browser.
    Attributes:
        env (EnvManager): Manages environment configuration loaded from a specified config file.
        logger (CustomLogger): Logger instance for structured logging throughout the retrieval process.
    Methods:
        get_link_and_key(race_id: str = None) -> tuple[str, str]:
            Launches a headless Chrome browser to navigate to the Race Monitor API page for the given
            race ID, captures browser performance logs, and extracts the WebSocket URL and the
            corresponding Sec-WebSocket-Key from network requests.
    """
    def __init__(self, caller_script: str, config_file_path: str, transaction_id: str = None):
        self.env = EnvManager(config_file_path)
        logging_config = self.env.config.get('logging_config', {})
        self.logger = CustomLogger(config=logging_config, logger_name=caller_script, transaction_id=transaction_id)
        formatted_config = "\n".join([f"{key}: {value}" for key, value in self.env.config.items() if 'API_KEY' not in key])
        self.logger.info("Environment variables and logger initialized successfully")
        self.logger.debug(f"Configuration values set:\n{formatted_config}")

    def validate_race_id(self, race_id: str = None) -> None:
        """
        Validates the provided race_id to ensure it is a string of digits or an integer.

        If race_id is not provided (None or empty), prompts the user for input.
        If race_id is an integer, attempts to convert it to a string.
        Logs relevant information and errors during the validation process.

        Args:
            race_id (str): The race ID to validate.

        Raises:
            ValueError: If race_id cannot be converted to a string of digits or is invalid.
        """
        if not race_id: 
            self.logger.info("No RaceID provided, prompting user for input")
            race_id = input("RaceID= ")
            self.logger.debug(f"User provided {race_id}")

        self.logger.info(f"Validating RaceID: {race_id}")
        self.logger.debug(f"Type of RaceID: {type(race_id)}")
        if isinstance(race_id, int):
            try:
                self.logger.info("Converting race_id to string")
                race_id = str(race_id)
            except ValueError:
                self.logger.error(f"Error converting race_id to string: {race_id}")
                self.logger.debug(f'\n{traceback.format_exc()}')
                raise ValueError(f"Invalid RaceID provided: {race_id}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                self.logger.debug(f'\n{traceback.format_exc()}')
                raise (str(e))
            self.logger.info(f"RaceID converted to string successfully")

        self.logger.info("Checking if RaceID is a valid string of digits")
        if isinstance(race_id, str) and not race_id.isdigit():
            self.logger.error(f"Invalid race_id provided: {race_id}")
            self.logger.error("race_id must be a string of digits or an integer")
            self.logger.debug(f"Invalid RaceID provided: {race_id}")
            raise ValueError(f"Invalid RaceID provided: {race_id}")

    def get_link_and_key(self, race_id: str = None) -> tuple[str, str]:
        """
        Retrieves the WebSocket link and Sec-WebSocket-Key for a given Race Monitor race ID.

        This method launches a headless Chrome browser using Selenium, navigates to the Race Monitor API
        page for the provided race ID, captures browser performance logs, and extracts the WebSocket URL
        and the corresponding Sec-WebSocket-Key from the network requests.

        Args:
            race_id (str, optional): The Race Monitor race ID. If not provided, prompts the user for input.

        Returns:
            tuple[str, str]: A tuple containing the WebSocket link and the Sec-WebSocket-Key.

        Raises:
            ValueError: If the race_id is invalid.
            ImportError: If Selenium is not installed.
            TimeoutException: If the page fails to load in time.
            Exception: For any other unexpected errors.
        """
        function_name = inspect.stack()[0][3]

        self.logger.info(f"Starting {function_name} process")
        self.logger.info('Validating if RaceID is provided')
        self.validate_race_id(race_id)
        self.logger.info("RaceID validated successfully")
        self.logger.debug(f"RaceID to be used: {race_id}")

        self.logger.info("Importing Selenium modules")
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import TimeoutException
        except ImportError as e:
            self.logger.error(f"Selenium is not installed: {e}")
            self.logger.debug(f'\n{traceback.format_exc()}')
            raise ImportError("Selenium is required for this method. Please install it via 'pip install selenium'.")
        except Exception as e:
            self.logger.error(f"Unexpected error importing Selenium: {e}")
            self.logger.debug(f'\n{traceback.format_exc()}')
            raise (str(e))
        self.logger.info("Selenium modules imported successfully")

        self.logger.info("Setting up Selenium WebDriver with headless Chrome")
        options = Options()
        options.add_argument("--headless")  
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")  
        options.add_argument("--disable-infobars")  
        options.add_argument("--disable-popup-blocking")  
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--incognito")
        self.logger.debug(f"Chrome options set: {options.arguments}")

        capabilities = options.to_capabilities()
        capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
        self.logger.debug(f"Chrome capabilities set: {capabilities}")

        self.logger.info("Initializing Chrome WebDriver")
        driver = webdriver.Chrome(options=options)
        
        self.logger.info(f"Navigating to Race Monitor API for RaceID: {race_id}")
        try:
            driver.get(f'https://api.race-monitor.com/Timing/?raceid={race_id}')
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))  
            )
            self.logger.info("Page loaded successfully") 
        except TimeoutException as e:
            self.logger.error(f"Timeout occurred while waiting for page to load: {e}")
            self.logger.debug(f'\n{traceback.format_exc()}')
            raise TimeoutException(f"Timeout while loading page for RaceID: {race_id}")
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            self.logger.debug(f'\n{traceback.format_exc()}')
            raise (str(e))

        self.logger.info("Retrieving performance logs")
        logs = driver.get_log("performance")
        self.logger.debug(f"Number of performance log entries retrieved: {len(logs)}")
        self.logger.debug(f"Performance logs: {logs}")

        self.logger.info("Searching for WebSocket link and Sec-WebSocket-Key in logs")
        wss_link = None
        for log in logs:
            message = log["message"]
            if "wss://" in message:
                wss_link = message
                break

        data = json.loads(wss_link)
        wss_link = data['message']['params']['url']    
        self.logger.debug(f"WebSocket link found: {wss_link}")

        for log in logs:
            message = log["message"] 
            if 'Sec-WebSocket-Key' in message:
                key_message = message
                break
        data = json.loads(key_message)
        wss_key = data['message']['params']['request']['headers']['Sec-WebSocket-Key']
        self.logger.debug(f"WebSocket key found: {wss_key}")

        self.logger.info("Closing WebDriver")
        driver.quit()
        
        del logs, data, key_message, message, options, capabilities, driver
        return wss_link, wss_key
