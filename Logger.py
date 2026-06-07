import logging
import os
import ConfigurationManager
from datetime import datetime
from rich.console import Console

_console = Console(stderr=True)

class Logger:
    """
    File logger with rich-powered console output.
    Writes structured .log files and prints coloured messages to stderr.
    """

    def __init__(self):
        log_dir  = ConfigurationManager.LOGS_FOLDER_PATH
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, datetime.now().strftime("%d-%m-%y") + ".log")

        self._logger = logging.getLogger(__name__ + log_file)
        if not self._logger.handlers:
            self._logger.setLevel(logging.INFO)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%d-%m-%y %I:%M:%S %p'
            ))
            self._logger.addHandler(fh)

    def info(self, message: str):
        self._logger.info(message)

    def error(self, message: str):
        self._logger.error(message)
        _console.print(f"[bold red]ERROR[/] {message}")