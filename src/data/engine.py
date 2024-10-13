import logging
import os

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine

load_dotenv(override=True)
log = logging.getLogger(__name__)

db_config = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "data": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

# Initialize the engine used to connect to the data
# See: https://docs.sqlalchemy.org/en/20/core/engines.html
engine_string = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['data']}"
engine: Engine = create_engine(engine_string)
