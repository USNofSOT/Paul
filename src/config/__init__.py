from __future__ import annotations
from dotenv import load_dotenv

from config.awards import *
from config.training import *
from config.main_server import *
from config.ranks_roles import *
from config.spd_servers import *
from config.subclasses import *
from config.netc_server import *
from config.synonyms import *

from src.config.ranks_roles import NSC_ROLE
from src.config.spd_servers import SPD_NSC_ROLE

load_dotenv()

NSC_ROLES = NSC_ROLE, SPD_NSC_ROLE  # roles from either main server or SPD server

MAX_MESSAGE_LENGTH = 2000
