from __future__ import annotations
from typing import Final
from dotenv import load_dotenv
import os

load_dotenv()

# TOKEN
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')


# GUILD ID for SPD Server
SPD_ID: Final[int]=971718695602778162

# Engine Room Channel ID
ENGINE_ROOM: Final[int]=1288304233409548309



# GUILD ID For Main Server
GUILD_ID: Final[int] = 933907909954371654
SPD_GUILD_ID: Final[int] = 971718695602778162
NETC_GUILD_ID: Final[int] = 1293725126562680985

# GUILD OWNER ID
GUILD_OWNER_ID: Final[int] = 215990848465141760

# MISC CHANNEL ID'S
TRAINING_RECORDS_CHANNEL: Final[int] = 0 # TODO: Add training records channel ID
ENGINE_ROOM: Final[int] = 1288304233409548309

# NETC CHANNEL ID'S
JLA_RECORDS_CHANNEL: Final[int] = 1125778657030447105
SNLA_RECORDS_CHANNEL: Final[int] = 1204525677249040455
OCS_RECORDS_CHANNEL: Final[int] = 1211255851520753674
SOCS_RECORDS_CHANNEL: Final[int] = 1076129424237412375
NETC_RECORDS_CHANNELS: Final[tuple[int, int, int, int]] = JLA_RECORDS_CHANNEL, SNLA_RECORDS_CHANNEL, OCS_RECORDS_CHANNEL, SOCS_RECORDS_CHANNEL

# NETC Role ID's
JLA_GRADUATE_ROLE: Final[int] = 1125781917954998273
SNLA_GRADUATE_ROLE: Final[int] = 1076140370309693521
OCS_GRADUATE_ROLE: Final[int] = 1076140392208146432
SOCS_GRADUATE_ROLE: Final[int] =  1076140400928104508
NETC_GRADUATE_ROLES: Final[tuple[int, int, int, int]] = JLA_GRADUATE_ROLE, SNLA_GRADUATE_ROLE, OCS_GRADUATE_ROLE, SOCS_GRADUATE_ROLE

# BOAT COMMAND CHANNEL ID'S
BC_LUSTY: Final[int]=995297017439977625
BC_AUDACIOUS: Final[int]=1164680390204739674
BC_MAELSTROM: Final[int]=1002304943291641896
BC_ADUN: Final[int]=1240784666835943525
BC_ADRESTIA: Final[int]=1084452484392697936
BC_HYPERION: Final[int]=1157426343777157270
BC_PLATYPUS: Final[int]=995299008987803719
BC_ARIZONA: Final[int]=1058850504630866050
BC_PHANTOM: Final[int]=1274254041823580225
BC_ORIGIN: Final[int]=995299843448770690
BC_VENOM: Final[int]=1237840915914297414
BC_COLLINS: Final[int]=1247403752210694197

# BOA is a side channel so that bot does not need to be in main boa channel
BC_BOA: Final[int]=1101193993909456956

# VOYAGE LOG CHANNEL
VOYAGE_LOGS: Final[int]=935343526626078850

#NCO COMMS
NCO_COMMS: Final[int]=935682287918546966

#Bot_Status
BOT_STATUS: Final[int]=1296034003480215552

# Roles
JE_ROLE = 933917171132825620 # Junior Enlisted
NCO_ROLE = 933917099867377684 # Non-Commissioned Officer
SNCO_ROLE = 933916952064315452 # Senior Non-Commissioned Officer
JO_ROLE = 933916865976213514 # Junior Officer
SO_ROLE = 933916762850877491 # Senior Officer
BOA_ROLE = 933914385099923497 # Board of Admirality

# Departments
NRC_ROLE = 944631719456284735 # NRC Department
NSC_ROLE = 1293725126562680985 # NSC Department
SPD_NSC_ROLE = 1288866599314395181 # NSC Department in SPD server

NSC_ROLES = NSC_ROLE, SPD_NSC_ROLE

# Subclass Synonyms
CARPENTER_SYNONYMS = ['carpenter', 'carp', 'bilge']
FLEX_SYNONYMS = ['flex', 'flexer', 'boarder']
CANNONEER_SYNONYMS = ['cannoneer', 'cannon', 'gunner', 'canonneer', 'cannons', 'mc']
HELM_SYNONYMS = ['helm', 'helmsman', 'navigator']
SURGEON_SYNONYMS = ['surgeon', 'doc', 'medic', 'field surgeon']
GRENADIER_SYNONYMS = ['grenadier', 'kegger', 'bomber']

# PERMISSIONS these are list with integers values, every integer value corresponds with a role\
# Note: For adding these you should declare them as followed @app_commands.checks.has_any_role(*SNCO_AND_UP)
JE_AND_UP = JE_ROLE, NCO_ROLE, SNCO_ROLE, JO_ROLE, SO_ROLE, BOA_ROLE, NSC_ROLE
NCO_AND_UP = NCO_ROLE, SNCO_ROLE, JO_ROLE, SO_ROLE, BOA_ROLE, NSC_ROLE
SNCO_AND_UP = SNCO_ROLE, JO_ROLE, SO_ROLE, BOA_ROLE, NSC_ROLE
JO_AND_UP = JO_ROLE, SO_ROLE, BOA_ROLE, NSC_ROLE
SO_AND_UP = SO_ROLE, BOA_ROLE, NSC_ROLE
BOA_NSC = BOA_ROLE, NSC_ROLE
