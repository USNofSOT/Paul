import glob
import logging
import os
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from discord.ext import commands

LOGS_DIR = './logs'

# # 1 for True, 0 for False
LOGS_PERSISTENCE : bool = bool(int(os.getenv('LOGS_PERSISTENCE', 1)))
# int value in days
LOGS_MAX_AGE_IN_DAYS : int = int(os.getenv('LOGS_MAX_AGE_IN_DAYS', 7))

_bot: Optional['commands.Bot'] = None


def register_bot(bot: 'commands.Bot'):
    global _bot
    _bot = bot


def get_bot() -> Optional['commands.Bot']:
    return _bot


def _notify_engineers(logger_name, level, msg, *args, **kwargs):
    bot = get_bot()
    if not bot:
        return

    from src.utils.discord_utils import send_engineer_log
    from src.utils.embeds import AlertSeverity
    import asyncio

    severity_map = {
        logging.DEBUG: AlertSeverity.INFO,
        logging.INFO: AlertSeverity.INFO,
        logging.WARNING: AlertSeverity.WARNING,
        logging.ERROR: AlertSeverity.ERROR,
        logging.CRITICAL: AlertSeverity.CRITICAL,
    }

    severity = severity_map.get(level, AlertSeverity.ERROR)

    # Format the message if there are args
    if args:
        try:
            formatted_msg = msg % args
        except Exception:
            formatted_msg = msg
    else:
        formatted_msg = msg

    # Get exception info if available
    exception = kwargs.get('exc_info')
    if exception:
        import sys
        exception = sys.exc_info()[1]
    elif not isinstance(exception, Exception):
        exception = None

    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            asyncio.create_task(
                send_engineer_log(
                    bot,
                    severity=severity,
                    title=f"Logger Alert: {logger_name}",
                    description=formatted_msg,
                    exception=exception,
                    notify_engineers=True
                )
            )
    except RuntimeError:
        # No running event loop, can't send discord message
        pass


def wrap_log_method(original_method, level):
    def wrapper(self, msg, *args, **kwargs):
        notify_engineer = kwargs.pop('notify_engineer', False)
        original_method(self, msg, *args, **kwargs)
        if notify_engineer:
            _notify_engineers(self.name, level, msg, *args, **kwargs)

    return wrapper


logging.Logger.error = wrap_log_method(logging.Logger.error, logging.ERROR)
logging.Logger.warning = wrap_log_method(logging.Logger.warning, logging.WARNING)
logging.Logger.info = wrap_log_method(logging.Logger.info, logging.INFO)
logging.Logger.debug = wrap_log_method(logging.Logger.debug, logging.DEBUG)
logging.Logger.critical = wrap_log_method(logging.Logger.critical, logging.CRITICAL)


class PaulLogger(logging.Logger):
    pass


logging.setLoggerClass(PaulLogger)
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