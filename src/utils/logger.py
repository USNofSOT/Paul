import glob
import logging
import os
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler

LOGS_DIR = './logs'

# # 1 for True, 0 for False
LOGS_PERSISTENCE : bool = bool(int(os.getenv('LOGS_PERSISTENCE', 1)))
# int value in days
LOGS_MAX_AGE_IN_DAYS : int = int(os.getenv('LOGS_MAX_AGE_IN_DAYS', 7))

log = logging.getLogger(__name__)


def initialise_logger():
    log.info('Initialising logger')
    if not os.path.exists(LOGS_DIR):
        log.info(f'Logs directory not found, creating directory: {LOGS_DIR}')
        os.makedirs(LOGS_DIR)

    if LOGS_PERSISTENCE:
        today = datetime.now().strftime('%Y-%m-%d')
        # General log handler
        general_handler = RotatingFileHandler(
            filename=f'{LOGS_DIR}/BOT-{int(datetime.now().timestamp())}.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
            encoding='utf-8',
        )

        # Error log handler
        error_handler = RotatingFileHandler(
            filename=f'{LOGS_DIR}/BOT-ERROR-{int(datetime.now().timestamp())}.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
        )
        error_handler.setLevel(logging.ERROR)

        logging.basicConfig(
            handlers=[general_handler, error_handler],
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        )
        log.info('Logger initialised')
        clean_logs()
    else:
        log.info('Logging is disabled due to LOGS_PERSISTENCE being set to False')

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

def clean_logs():
    log.info('Attempting to clean logs with expiration date of %s days' % LOGS_MAX_AGE_IN_DAYS)
    expiration_date = time.time() - LOGS_MAX_AGE_IN_DAYS * 86400
    entries = os.listdir(LOGS_DIR)

    log.info(f'Found {len(entries)} log files')
    for entry in entries:
        time_created = os.stat(os.path.join(LOGS_DIR, entry)).st_ctime
        if time_created < expiration_date:
            try:
                log.info('Deleted for exceeding expiration limit : %s' % (LOGS_DIR + '/' + entry))
                os.remove(LOGS_DIR + '/' + entry)
            except Exception as e:
                log.error('%s' % e)