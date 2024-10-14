from __future__ import annotations
from typing import Final
from dotenv import load_dotenv
import os

load_dotenv()

# TOKEN
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

# GUILD ID
GUILD_ID: Final[int] = 933907909954371654

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

# Subclass Synonyms
CARPENTER_SYNONYMS = ['carpenter', 'carp', 'bilge']
FLEX_SYNONYMS = ['flex', 'flexer', 'boarder']
CANNONEER_SYNONYMS = ['cannoneer', 'cannon', 'gunner', 'canonneer', 'cannons']
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
BOA_AND_UP = BOA_ROLE, NSC_ROLE
