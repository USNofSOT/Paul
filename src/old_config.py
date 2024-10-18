from __future__ import annotations
from typing import Final
from dotenv import load_dotenv
import os

from data.structs import Award

load_dotenv()

# TOKEN
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')


# GUILD ID for SPD Server
SPD_ID: Final[int]=971718695602778162

# Engine Room Channel ID
ENGINE_ROOM: Final[int]=1288304233409548309



# GUILD ID For Main Server
GUILD_ID: Final[int] = 933907909954371654
SPD_GUID_ID: Final[int] = 971718695602778162

# GUILD OWNER ID
GUILD_OWNER_ID: Final[int] = 215990848465141760

# MISC CHANNEL ID'S
ENGINE_ROOM: Final[int] = 1288304233409548309

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

E1_ROLES = [933913081099214848] # Recruit
E2_ROLES = [933913010806857801, 1201933589357547540] # Seaman, Seaman Apprentice
E3_ROLES = [933912647999565864] # Able Seaman
E4_ROLES = [933912557008343120] # Junior Petty Officer
E5_ROLES = [] # Unused
E6_ROLES = [933911949585035275] # Petty Officer
E7_ROLES = [933911464660570132] # Chief Petty Officer
E8_ROLES = [933911373669335092] # Senior Chief Petty Officer
O1_ROLES = [933910558695129118] # Midshipman
O2_ROLES = [] # Unused
O3_ROLES = [933910174555598879] # Lieutenant
O4_ROLES = [933909957437423677] # Lieutenant Commander
O5_ROLES = [933909780639150101] # Commander
O6_ROLES = [933909668550553630] # Captain
O7_ROLES = [933909182711746570] # Commodore
O8_ROLES = [1157429131416449134] # Rear Admiral

O8_AND_UP = O8_ROLES + [BOA_ROLE] # some overlap, but includes BOA members without ranks
O7_AND_UP = O7_ROLES + O8_AND_UP
O6_AND_UP = O6_ROLES + O7_AND_UP
O5_AND_UP = O5_ROLES + O6_AND_UP
O4_AND_UP = O4_ROLES + O5_AND_UP
O3_AND_UP = O3_ROLES + O4_AND_UP
O2_AND_UP = O2_ROLES + O3_AND_UP
O1_AND_UP = O1_ROLES + O2_AND_UP
E8_AND_UP = E8_ROLES + O1_AND_UP
E7_AND_UP = E7_ROLES + E8_AND_UP
E6_AND_UP = E6_ROLES + E7_AND_UP
E5_AND_UP = E5_ROLES + E6_AND_UP
E4_AND_UP = E4_ROLES + E5_AND_UP
E3_AND_UP = E3_ROLES + E4_AND_UP
E2_AND_UP = E2_ROLES + E3_AND_UP
E1_AND_UP = E1_ROLES + E2_AND_UP

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

# AWARDS INFO
## Medals And Ribbons - Voyage Medals
CITATION_OF_VOAYGES = Award(
    role_id=934090102735536188,
    embed_id=1292514303936561183,
    ranks_responsible="E-6+",
    threshold=5
)
LEGION_OF_VOYAGES = Award(
    role_id=983412707912998942,
    embed_id=1292514303936561183,
    ranks_responsible="E-7+",
    threshold=25
)
VOYAGE_MEDALS = (CITATION_OF_VOAYGES, LEGION_OF_VOYAGES)

MEDALS_AND_RIBBONS = {
    'voyages': VOYAGE_MEDALS,
}
'''
CITATION_OF_VOAYGES = {
    'minimum': 5,
    'ranks responsible': E6_AND_UP,
    'role': 934090102735536188,
}
LEGION_OF_VOYAGES = {
    'minimum': 25,
    'ranks responsible': E7_AND_UP,
    'role': 983412707912998942,
}
HONORABLE_VOYAGER_MEDAL = {
    'minimum': 50,
    'ranks responsible': O1_AND_UP,
    'role': 1059271717836566588,
}
MERITORIOUS_VOYAGER_MEDAL = {
    'minimum': 100,
    'ranks responsible': O4_AND_UP,
    'role': 1059240151852797993,
}
ADMIRABLE_VOYAGER_MEDAL = {
    'minimum': 200,
    'ranks responsible': O7_AND_UP,
    'role': 1140637598457544857,
}
# Medals must be ordered lowest to highest voyage count
VOYAGE_MEDALS = (CITATION_OF_VOAYGES, LEGION_OF_VOYAGES, HONORABLE_VOYAGER_MEDAL, 
                 MERITORIOUS_VOYAGER_MEDAL, ADMIRABLE_VOYAGER_MEDAL)


MEDALS_AND_RIBBONS = {
    'voyages': VOYAGE_MEDALS,
}
'''
