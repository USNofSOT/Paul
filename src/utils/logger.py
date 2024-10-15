import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

LOGS_DIR = '../logs'

log = logging.getLogger(__name__)


def initialise_logger():
    log.info('Initialising logger')
    if not os.path.exists(LOGS_DIR):
        log.info(f'Logs directory not found, creating directory: {LOGS_DIR}')
        os.makedirs(LOGS_DIR)

    # General log handler
    general_handler = RotatingFileHandler(
        filename=f'{LOGS_DIR}/BOT-{int(datetime.now().timestamp())}.log',
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=10,  # Keep 10 backup files
    )

    # Error log handler
    error_handler = RotatingFileHandler(
        filename=f'{LOGS_DIR}/BOT-ERROR-{int(datetime.now().timestamp())}.log',
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=25,  # Keep 25 backup files
    )
    error_handler.setLevel(logging.ERROR)

    logging.basicConfig(
        handlers=[general_handler, error_handler],
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    )
    log.info('Logger initialised')