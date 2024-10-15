import glob
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

    today = datetime.now().strftime('%Y-%m-%d')
    # General log handler
    general_handler = RotatingFileHandler(
        filename=f'{LOGS_DIR}/BOT-{today}.log',
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,  # Keep 10 backup files
        encoding='utf-8',
    )

    # Error log handler
    error_handler = RotatingFileHandler(
        filename=f'{LOGS_DIR}/BOT-ERROR-{int(datetime.now().timestamp())}.log',
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,  # Keep 25 backup files
    )
    error_handler.setLevel(logging.ERROR)

    logging.basicConfig(
        handlers=[general_handler, error_handler],
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    )
    log.info('Logger initialised')

def get_most_recent_log_file():
    log_files = glob.glob(os.path.join(LOGS_DIR, 'BOT-[!ERROR]*.log'))
    if not log_files:
        return None
    most_recent_log = max(log_files, key=os.path.getctime)
    return most_recent_log

def get_most_recent_error_log_file():
    error_log_files = glob.glob(os.path.join(LOGS_DIR, 'BOT-ERROR-*.log'))
    if not error_log_files:
        return None
    most_recent_error_log = max(error_log_files, key=os.path.getctime)
    return most_recent_error_log