# author : Gabriel Santini Francisco
# email  : gabrielsantinifrancisco@outlook.com

# Description: 
# Retrieves the WebSocket link and Sec-WebSocket-Key for a given Race Monitor race ID
# by launching a headless Chrome browser, navigating to the Race Monitor API page,
# capturing browser performance logs, and extracting the relevant WebSocket connection
# information from the network requests. Useful for automating access to real-time
# race data streams that require dynamic WebSocket authentication.


from selenium import webdriver                                      
from selenium.webdriver.chrome.options import Options               
from selenium.webdriver.common.by import By                         
from selenium.webdriver.support.ui import WebDriverWait             
from selenium.webdriver.support import expected_conditions as EC    
from selenium.common.exceptions import TimeoutException             
from CustomLogger import CustomLogger 
from EnvManager import EnvManager 
import json, os, sys, inspect, traceback

def GetLinkAndKey(race_id: str = None) -> tuple[str, str]:
    """
    Retrieves the WebSocket link and Sec-WebSocket-Key for a given Race Monitor race ID.
    This function uses Selenium WebDriver to navigate to the Race Monitor API page for the specified
    race ID, captures browser performance logs, and extracts the WebSocket URL and the corresponding
    Sec-WebSocket-Key from the network requests.
    Args:
        race_id (str, optional): The Race Monitor race ID. If not provided, the user will be prompted to input it.
    Returns:
        tuple[str, str]: A tuple containing the WebSocket link (str) and the Sec-WebSocket-Key (str).
                            Returns (None, None) if an error occurs during the process.
    """
    function_name = inspect.stack()[0][3]

    logger.info(f"Starting {function_name} process")
    options = Options()
    options.add_argument("--headless")  
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")  
    options.add_argument("--disable-infobars")  
    options.add_argument("--disable-popup-blocking")  
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--incognito")
    logger.debug(f"Chrome options set: {options.arguments}")

    capabilities = options.to_capabilities()
    capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
    logger.debug(f"Chrome capabilities set: {capabilities}")

    logger.info("Initializing Chrome WebDriver")
    driver = webdriver.Chrome(options=options)

    logger.info('Validating if RaceID is provided')
    if not race_id: 
        logger.info("No RaceID provided, prompting user for input")
        race_id = input("RaceID= ")
        logger.debug(f"User provided {race_id}")
    elif isinstance(race_id, int):
        logger.warning("race_id must be a string converting integer to string")
        logger.debug(f"Converting race_id to string: {race_id}")
        race_id = str(race_id)
    else:
        logger.error("race_id must be a string of digits or an integer")
        logger.debug(f"Invalid race_id provided: {race_id}")
        return None, None


    logger.info(f"Navigating to Race Monitor API for RaceID: {race_id}")
    try:
        driver.get(f'https://api.race-monitor.com/Timing/?raceid={race_id}')
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))  
        )
        logger.info("Page loaded successfully") 
    except TimeoutException as e:
        logger.error(f"Timeout occurred while waiting for page to load: {e}")
        logger.debug(f'\n{traceback.format_exc()}')
        return None, None
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.debug(f'\n{traceback.format_exc()}')
        return None, None

    logger.info("Retrieving performance logs")
    logs = driver.get_log("performance")
    logger.debug(f"Number of performance log entries retrieved: {len(logs)}")
    logger.debug(f"Performance logs: {logs}")

    logger.info("Searching for WebSocket link and Sec-WebSocket-Key in logs")
    wss_link = None
    for log in logs:
        message = log["message"]
        if "wss://" in message:
            wss_link = message
            break

    data = json.loads(wss_link)
    wss_link = data['message']['params']['url']    
    logger.debug(f"WebSocket link found: {wss_link}")

    for log in logs:
        message = log["message"] 
        if 'Sec-WebSocket-Key' in message:
            key_message = message
            break
    data = json.loads(key_message)
    wss_key = data['message']['params']['request']['headers']['Sec-WebSocket-Key']
    logger.debug(f"WebSocket key found: {wss_key}")

    logger.info("Closing WebDriver")
    driver.quit()
    
    del logs, data, key_message, message, options, capabilities, driver
    return wss_link, wss_key

##########################
# DEFAULT EXECUTION
##########################
global logger, config_file_path
script_dir          = os.path.dirname(os.path.abspath(__file__))
script_name         = os.path.splitext(os.path.basename(sys.argv[0]))[0]
config_file_path    = os.path.join(script_dir, '..', 'conf', f'{script_name}.cfg')
env                 = EnvManager(config_file_path)

# Initialize logger
logging_config      = env.config.get('logging_config', {})
logger              = CustomLogger(config=logging_config, logger_name=script_name)
formatted_config    = "\n".join([f"{key}: {value}" for key, value in env.config.items() if 'API_KEY' not in key])
logger.info("Environment variables and logger initialized successfully")
logger.debug(f"Configuration values set:\n{formatted_config}")

if __name__ == "__main__": print(GetLinkAndKey())