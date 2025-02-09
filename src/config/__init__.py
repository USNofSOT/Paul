from __future__ import annotations

from config.awards import *
from config.main_server import *
from config.netc_server import *
from config.ranks_roles import *
from config.requirements import *
from config.spd_servers import *
from config.subclasses import *
from config.synonyms import *
from config.training import *
from dotenv import load_dotenv

from src.config.ranks_roles import NSC_ROLE
from src.config.spd_servers import SPD_NSC_ROLE

load_dotenv()

NSC_ROLES = NSC_ROLE, SPD_NSC_ROLE  # roles from either main server or SPD server

ENGINEERS = [281119159012556800, 646516242949341236]  # Discord IDs of engineers
MAX_MESSAGE_LENGTH = 2000
MAX_NICKNAME_LENGTH = 32
