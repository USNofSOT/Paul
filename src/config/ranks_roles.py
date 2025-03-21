from collections import OrderedDict
from enum import Enum

###############################################################################
# Rank Roles
###############################################################################
JE_ROLE = 933917171132825620  # Junior Enlisted
NCO_ROLE = 933917099867377684  # Non-Commissioned Officer
SNCO_ROLE = 933916952064315452  # Senior Non-Commissioned Officer
JO_ROLE = 933916865976213514  # Junior Officer
SO_ROLE = 933916762850877491  # Senior Officer
BOA_ROLE = 933914385099923497  # Board of Admirality


###############################################################################
# Ranks
###############################################################################
DH_ROLES = [1003446066835894394]  # Deckhand
E1_ROLES = [933913081099214848]  # Recruit
E2_ROLES = [933913010806857801, 1201933589357547540]  # Seaman, Seaman Apprentice
E3_ROLES = [933912647999565864]  # Able Seaman
VT_ROLES = [1218962980536848494]  # Veteran
E4_ROLES = [933912557008343120]  # Junior Petty Officer
E5_ROLES = []  # Unused
E6_ROLES = [933911949585035275]  # Petty Officer
E7_ROLES = [933911464660570132]  # Chief Petty Officer
E8_ROLES = [933911373669335092]  # Senior Chief Petty Officer
O1_ROLES = [933910558695129118]  # Midshipman
O2_ROLES = []  # Unused
O3_ROLES = [933910174555598879]  # Lieutenant
O4_ROLES = [933909957437423677]  # Lieutenant Commander
O5_ROLES = [933909780639150101]  # Commander
O6_ROLES = [933909668550553630]  # Captain
O7_ROLES = [933909182711746570]  # Commodore
O8_ROLES = [1157429131416449134]  # Rear Admiral
MCPON_ROLES = [1002280798801625179]  # Master Chief Petty Officer of the Navy
VADM_ROLES = [933914222088306698]  # Vice Admiral of the Navy
AOTN_ROLES = [933914043935248424]  # Admiral of the Navy
RT_ROLES = [958152319424413726]  # Retired

###############################################################################
# Command Roles
###############################################################################
FLEET_CO_ROLE = 1250612616510967899
SHIP_CO_ROLE = 1250613478503350403
SHIP_FO_ROLE = 1250613812336398418
SHIP_COS_ROLE = 1250613959095091343
SHIP_SL_ROLE = 1143324589968068619


class COC_ENUM(Enum):  # noqa: N801
    Navy = 0
    Fleet = 1
    Ship = 2
    Squad = 3

    # CMD ROLE       # CO ROLE      # COMMON GROUP


CHAIN_OF_COMMAND = OrderedDict(
    [
        (AOTN_ROLES[0], (None, COC_ENUM.Navy.value)),
        (VADM_ROLES[0], (AOTN_ROLES[0], COC_ENUM.Navy.value)),
        (MCPON_ROLES[0], (AOTN_ROLES[0], COC_ENUM.Navy.value)),
        (FLEET_CO_ROLE, (VADM_ROLES[0], COC_ENUM.Navy.value)),
        (SHIP_CO_ROLE, (FLEET_CO_ROLE, COC_ENUM.Fleet.value)),
        (SHIP_FO_ROLE, (SHIP_CO_ROLE, COC_ENUM.Ship.value)),
        (SHIP_COS_ROLE, (SHIP_FO_ROLE, COC_ENUM.Ship.value)),
        (SHIP_SL_ROLE, (SHIP_COS_ROLE, COC_ENUM.Ship.value)),
        (SNCO_ROLE, (SHIP_SL_ROLE, COC_ENUM.Squad.value)),
        (NCO_ROLE, (SHIP_SL_ROLE, COC_ENUM.Squad.value)),
        (E3_ROLES[0], (SHIP_SL_ROLE, COC_ENUM.Squad.value)),  # Able Seaman
        (E2_ROLES[0], (SHIP_SL_ROLE, COC_ENUM.Squad.value)),  # Seaman
        (E2_ROLES[1], (VADM_ROLES[0], COC_ENUM.Navy.value)),  # Seaman Apprentice
        (E1_ROLES[0], (VADM_ROLES[0], COC_ENUM.Navy.value)),  # Recruit
    ]
)

###############################################################################
# SPD Roles
###############################################################################
NETC_ROLE = 1034233491707150376  # NETC Department
NSC_ROLE = 1293725126562680985  # NSC Department
NRC_ROLE = 944631719456284735  # NRC Department
SCHEDULING_ROLE = 972551831655956580  # Scheduling Department
LOGISTICS_ROLE = 1001313951931441172  # Logistics Department
MEDIA_ROLE = 1083502355506540624  # Media Department

SPD_ROLES = [NETC_ROLE, NSC_ROLE, NRC_ROLE, SCHEDULING_ROLE, LOGISTICS_ROLE, MEDIA_ROLE]

###############################################################################
# Permissions
###############################################################################
# PERMISSIONS these are list with integers values, every integer value corresponds with a role\
# Note: For adding these you should declare them as followed
# @app_commands.checks.has_any_role(*SNCO_AND_UP)
JE_AND_UP = JE_ROLE, NCO_ROLE, SNCO_ROLE, JO_ROLE, SO_ROLE, BOA_ROLE, NSC_ROLE
NCO_AND_UP = NCO_ROLE, SNCO_ROLE, JO_ROLE, SO_ROLE, BOA_ROLE, NSC_ROLE
SNCO_AND_UP = SNCO_ROLE, JO_ROLE, SO_ROLE, BOA_ROLE, NSC_ROLE
JO_AND_UP = JO_ROLE, SO_ROLE, BOA_ROLE, NSC_ROLE
SO_AND_UP = SO_ROLE, BOA_ROLE, NSC_ROLE
BOA_NSC = BOA_ROLE, NSC_ROLE

# Pure roles list without any additional permissions (e.g. NSC)
NCO_AND_UP_PURE = NCO_ROLE, SNCO_ROLE, JO_ROLE, SO_ROLE, BOA_ROLE

O8_AND_UP = O8_ROLES + [
    BOA_ROLE
]  # some overlap, but includes BOA members without ranks
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

###############################################################################
# Misc
###############################################################################
MARINE_ROLE = 1169308325586931753
USMC_ROLE = 1164156272707383297
VOYAGE_PERMISSIONS = 935340203965567006
