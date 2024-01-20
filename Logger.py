import logging
import ConfigurationManager
from datetime import datetime

class Logger:
    """
    A simple logger class for logging information and errors to a file.

    Usage:
    logger = Logger()
    logger.info("This is an information message.")
    logger.error("This is an error message.")
    """

    logger = logging.getLogger(__name__)
    file_handler = logging.FileHandler(ConfigurationManager.LOGS_FOLDER_PATH + "/" + datetime.now().strftime("%d-%m-%y") + ".log")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%y %I:%M:%S %p')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    file_handler.close()

    def info(self, message):
        """
        Log an information message.

        Parameters:
        - message: The information message to be logged.
        """
        self.logger.info(message)

    def error(self, message):
        """
        Log an error message.

        Parameters:
        - message: The error message to be logged.
        """
        self.logger.error(message)
