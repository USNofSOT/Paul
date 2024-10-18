###############################################################################
# Rank Roles
###############################################################################
JE_ROLE = 933917171132825620 # Junior Enlisted
NCO_ROLE = 933917099867377684 # Non-Commissioned Officer
SNCO_ROLE = 933916952064315452 # Senior Non-Commissioned Officer
JO_ROLE = 933916865976213514 # Junior Officer
SO_ROLE = 933916762850877491 # Senior Officer
BOA_ROLE = 933914385099923497 # Board of Admirality


###############################################################################
# Ranks
###############################################################################
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

#def rank_to_roles(rank_str : str) -> list[int] | None:
#    if rank_str = 

###############################################################################
# SPD Roles
###############################################################################
NSC_ROLE = 1293725126562680985 # NSC Department
NRC_ROLE = 944631719456284735 # NRC Department

###############################################################################
# Permissions
###############################################################################
# PERMISSIONS these are list with integers values, every integer value corresponds with a role\
# Note: For adding these you should declare them as followed @app_commands.checks.has_any_role(*SNCO_AND_UP)
JE_AND_UP = JE_ROLE, NCO_ROLE, SNCO_ROLE, JO_ROLE, SO_ROLE, BOA_ROLE, NSC_ROLE
NCO_AND_UP = NCO_ROLE, SNCO_ROLE, JO_ROLE, SO_ROLE, BOA_ROLE, NSC_ROLE
SNCO_AND_UP = SNCO_ROLE, JO_ROLE, SO_ROLE, BOA_ROLE, NSC_ROLE
JO_AND_UP = JO_ROLE, SO_ROLE, BOA_ROLE, NSC_ROLE
SO_AND_UP = SO_ROLE, BOA_ROLE, NSC_ROLE
BOA_NSC = BOA_ROLE, NSC_ROLE