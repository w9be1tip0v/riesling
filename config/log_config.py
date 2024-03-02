import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
import os

# Configure logging
def setup_logging():
    # Set the root directory path
    root_dir_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))     # Get the parent directory of the current file

    # Path to the .log directory 
    log_directory = os.path.join(root_dir_path, '.log')

    # Create the .log directory if it does not exist
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Log file name with the current date
    log_filename = os.path.join(log_directory, f"polygon_api_{datetime.now().strftime('%Y-%m-%d')}.log")

    # Set up logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Set up a TimedRotatingFileHandler
    handler = TimedRotatingFileHandler(
    log_filename,  # Log file name
    when='midnight',  # Split the log file at midnight
    interval=1,  # Split the log file every day
    backupCount=30,  # Keep 30 log files
    encoding='utf-8',  # Set the encoding to UTF-8
    delay=False,  # Write log messages immediately
    utc=False,  # Use local time
    )

    # Set the log message format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # Set the log message format
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger