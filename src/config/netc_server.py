from typing import Final

# GUILD ID for SPD Server
NETC_GUILD_ID: Final[int] = 1076129419812421692

###############################################################################
# RECORDS CHANNELS
###############################################################################
JLA_RECORDS_CHANNEL: Final[int] = 1125778657030447105
SNLA_RECORDS_CHANNEL: Final[int] = 1204525677249040455
SLA_RECORDS_CHANNEL: Final[int] = 1471663660060512487
COSA_RECORDS_CHANNEL: Final[int] = 1471666458793873438
OCS_RECORDS_CHANNEL: Final[int] = 1211255851520753674
SOCS_RECORDS_CHANNEL: Final[int] = 1076129424237412375

###############################################################################
# MISC CHANNELS
###############################################################################
NETC_BOT_CHANNEL: Final[int] = 1332005703262404642

###############################################################################
# INSTRUCTOR ROLES
###############################################################################
JLA_INSTRUCTOR_ROLE: Final[int] = 1125780575572201522
SNLA_INSTRUCTOR_ROLE: Final[int] = 1076129419841773645
SLA_INSTRUCTOR_ROLE: Final[int] = 1471675392023859200
COSA_INSTRUCTOR_ROLE: Final[int] = 1471675547317964943
OCS_INSTRUCTOR_ROLE: Final[int] = 1076129419841773646
SOCS_INSTRUCTOR_ROLE: Final[int] = 1076129419841773647

###############################################################################
# GRADUATE ROLES
###############################################################################
JLA_GRADUATE_ROLE: Final[int] = 1125781917954998273
SNLA_GRADUATE_ROLE: Final[int] = 1076140370309693521
SLA_GRADUATE_ROLE: Final[int] = 1471682430497984633
COSA_GRADUATE_ROLE: Final[int] = 1471682545883287757
OCS_GRADUATE_ROLE: Final[int] = 1076140392208146432
SOCS_GRADUATE_ROLE: Final[int] =  1076140400928104508

# Each curriculum is defined once here so active/legacy handling remains a
# configuration change even if archived roles or channels are later removed.
NETC_ACTIVE_CURRICULUMS: Final[tuple[tuple[str, int, int, int], ...]] = (
    ("JLA", JLA_RECORDS_CHANNEL, JLA_INSTRUCTOR_ROLE, JLA_GRADUATE_ROLE),
    ("SLA", SLA_RECORDS_CHANNEL, SLA_INSTRUCTOR_ROLE, SLA_GRADUATE_ROLE),
    ("COSA", COSA_RECORDS_CHANNEL, COSA_INSTRUCTOR_ROLE, COSA_GRADUATE_ROLE),
    ("OCS", OCS_RECORDS_CHANNEL, OCS_INSTRUCTOR_ROLE, OCS_GRADUATE_ROLE),
    ("SOCS", SOCS_RECORDS_CHANNEL, SOCS_INSTRUCTOR_ROLE, SOCS_GRADUATE_ROLE),
)
NETC_LEGACY_CURRICULUMS: Final[tuple[tuple[str, int, int, int], ...]] = (
    ("SNLA", SNLA_RECORDS_CHANNEL, SNLA_INSTRUCTOR_ROLE, SNLA_GRADUATE_ROLE),
)
ALL_NETC_CURRICULUMS: Final[tuple[tuple[str, int, int, int], ...]] = (
        NETC_ACTIVE_CURRICULUMS + NETC_LEGACY_CURRICULUMS
)

# Active curricula should live here. Historical/archived channels stay in the
# legacy group so they remain addressable without being treated as current.
NETC_RECORDS_CHANNELS: Final[tuple[int, ...]] = tuple(
    channel_id for _, channel_id, _, _ in NETC_ACTIVE_CURRICULUMS
)
LEGACY_NETC_RECORDS_CHANNELS: Final[tuple[int, ...]] = tuple(
    channel_id for _, channel_id, _, _ in NETC_LEGACY_CURRICULUMS
)
ALL_NETC_RECORDS_CHANNELS: Final[tuple[int, ...]] = (
        NETC_RECORDS_CHANNELS + LEGACY_NETC_RECORDS_CHANNELS
)
NETC_INSTRUCTOR_ROLES: Final[tuple[int, ...]] = tuple(
    instructor_role for _, _, instructor_role, _ in NETC_ACTIVE_CURRICULUMS
)
LEGACY_NETC_INSTRUCTOR_ROLES: Final[tuple[int, ...]] = tuple(
    instructor_role for _, _, instructor_role, _ in NETC_LEGACY_CURRICULUMS
)
NETC_GRADUATE_ROLES: Final[tuple[int, ...]] = tuple(
    graduate_role for _, _, _, graduate_role in NETC_ACTIVE_CURRICULUMS
)
LEGACY_NETC_GRADUATE_ROLES: Final[tuple[int, ...]] = tuple(
    graduate_role for _, _, _, graduate_role in NETC_LEGACY_CURRICULUMS
)

###############################################################################
# MISC ROLES
###############################################################################
CO_OF_NETC_ROLE: Final[int] = 1076129420043100183
XO_OF_NETC_ROLE: Final[int] = 1076129420005359641
HIGH_COMMAND_OF_NETC_ROLES = CO_OF_NETC_ROLE, XO_OF_NETC_ROLE
