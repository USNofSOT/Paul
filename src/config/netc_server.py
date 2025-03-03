from typing import Final

# GUILD ID for SPD Server
NETC_GUILD_ID: Final[int] = 1076129419812421692

###############################################################################
# RECORDS CHANNELS
###############################################################################
JLA_RECORDS_CHANNEL: Final[int] = 1125778657030447105
SNLA_RECORDS_CHANNEL: Final[int] = 1204525677249040455
OCS_RECORDS_CHANNEL: Final[int] = 1211255851520753674
SOCS_RECORDS_CHANNEL: Final[int] = 1076129424237412375
NETC_RECORDS_CHANNELS: Final[tuple[int, int, int, int]] = JLA_RECORDS_CHANNEL, SNLA_RECORDS_CHANNEL, OCS_RECORDS_CHANNEL, SOCS_RECORDS_CHANNEL

###############################################################################
# MISC CHANNELS
###############################################################################
NETC_BOT_CHANNEL: Final[int] = 1332005703262404642

###############################################################################
# INSTRUCTOR ROLES
###############################################################################
JLA_INSTRUCTOR_ROLE: Final[int] = 1125780575572201522
SNLA_INSTRUCTOR_ROLE: Final[int] = 1076129419841773645
OCS_INSTRUCTOR_ROLE: Final[int] = 1076129419841773646
SOCS_INSTRUCTOR_ROLE: Final[int] = 1076129419841773647

###############################################################################
# GRADUATE ROLES
###############################################################################
JLA_GRADUATE_ROLE: Final[int] = 1125781917954998273
SNLA_GRADUATE_ROLE: Final[int] = 1076140370309693521
OCS_GRADUATE_ROLE: Final[int] = 1076140392208146432
SOCS_GRADUATE_ROLE: Final[int] =  1076140400928104508
NETC_GRADUATE_ROLES: Final[tuple[int, int, int, int]] = JLA_GRADUATE_ROLE, SNLA_GRADUATE_ROLE, OCS_GRADUATE_ROLE, SOCS_GRADUATE_ROLE

###############################################################################
# MISC ROLES
###############################################################################
CO_OF_NETC_ROLE: Final[int] = 1076129420043100183
XO_OF_NETC_ROLE: Final[int] = 1076129420005359641
HIGH_COMMAND_OF_NETC_ROLES = CO_OF_NETC_ROLE, XO_OF_NETC_ROLE
