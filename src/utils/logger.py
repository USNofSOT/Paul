import glob
import logging
import os
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Callable, Optional

LOGS_DIR = './logs'

# # 1 for True, 0 for False
LOGS_PERSISTENCE : bool = bool(int(os.getenv('LOGS_PERSISTENCE', 1)))
# int value in days
LOGS_MAX_AGE_IN_DAYS : int = int(os.getenv('LOGS_MAX_AGE_IN_DAYS', 7))

log = logging.getLogger(__name__)

# Callback function to handle notifications instantly
_NOTIFICATION_CALLBACK: Optional[Callable[[logging.LogRecord], None]] = None


def set_notification_callback(callback: Callable[[logging.LogRecord], None]):
    """Set the callback function for engineer notifications."""
    global _NOTIFICATION_CALLBACK
    _NOTIFICATION_CALLBACK = callback


class NotifyEngineerHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        if getattr(record, 'notify_engineer', False) and _NOTIFICATION_CALLBACK:
            try:
                _NOTIFICATION_CALLBACK(record)
            except Exception as e:
                # Use standard print or a separate logger to avoid recursion
                print(f"Error in NotifyEngineerHandler callback: {e}")

def initialise_logger():
    # Register the NotifyEngineerHandler first so it catches all subsequent logs
    notify_handler = NotifyEngineerHandler()

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear any existing handlers to prevent duplication or conflicts with basicConfig
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(notify_handler)

    # Create logs directory if it doesn't exist
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))
    root_logger.addHandler(console_handler)

    log.info('Initialising logger')

    if LOGS_PERSISTENCE:
        today = datetime.now().strftime('%Y-%m-%d')
        target_dir = os.path.join(LOGS_DIR, today)

        if not os.path.exists(target_dir):
            log.info(f'Creating daily log directory: {target_dir}')
            os.makedirs(target_dir)

        # General log handler
        general_handler = RotatingFileHandler(
            filename=f'{target_dir}/BOT-{int(datetime.now().timestamp())}.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
            encoding='utf-8',
        )
        general_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))

        # Error log handler
        error_handler = RotatingFileHandler(
            filename=f'{target_dir}/BOT-ERROR-{int(datetime.now().timestamp())}.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))

        root_logger.addHandler(general_handler)
        root_logger.addHandler(error_handler)

        log.info('Logger initialised with file persistence in %s' % target_dir)
        clean_logs()
    else:
        log.info('Logging is disabled due to LOGS_PERSISTENCE being set to False')

def get_most_recent_log_file():
    log_files = glob.glob(os.path.join(LOGS_DIR, '**', 'BOT-[!ERROR]*.log'), recursive=True)
    if not log_files:
        return None
    most_recent_log = max(log_files, key=os.path.getctime)
    return most_recent_log

def get_most_recent_error_log_file():
    error_log_files = glob.glob(os.path.join(LOGS_DIR, '**', 'BOT-ERROR-*.log'), recursive=True)
    if not error_log_files:
        return None
    most_recent_error_log = max(error_log_files, key=os.path.getctime)
    return most_recent_error_log

def clean_logs():
    log.info('Attempting to clean logs with expiration date of %s days' % LOGS_MAX_AGE_IN_DAYS)
    expiration_limit = time.time() - (LOGS_MAX_AGE_IN_DAYS * 86400)

    if not os.path.exists(LOGS_DIR):
        return

    # Walk through the logs directory bottom-up to handle file deletion before directory deletion
    for root, dirs, files in os.walk(LOGS_DIR, topdown=False):
        for name in files:
            file_path = os.path.join(root, name)
            try:
                # Check creation time
                if os.path.getctime(file_path) < expiration_limit:
                    log.info(f'Deleting expired log file: {file_path}')
                    os.remove(file_path)
            except Exception as e:
                log.error(f'Failed to delete log file {file_path}: {e}')

        # After cleaning files, check if directory is empty and should be removed
        # Don't remove the root LOGS_DIR itself
        if root != LOGS_DIR and not os.listdir(root):
            try:
                log.info(f'Removing empty log directory: {root}')
                os.rmdir(root)
            except Exception as e:
                log.error(f'Failed to remove empty directory {root}: {e}')
