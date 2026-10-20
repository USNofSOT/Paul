from config import BOA_ROLE
from config import O8_AND_UP,O7_AND_UP, O6_AND_UP,O5_AND_UP,O4_AND_UP
from config import O8_ROLES,O7_ROLES,O6_ROLES,O5_ROLES,O4_ROLES
from config import O3_AND_UP,O2_AND_UP,O1_AND_UP
from config import O3_ROLES,O2_ROLES,O1_ROLES
from config import E8_AND_UP,E7_AND_UP,E6_AND_UP,E5_AND_UP,E4_AND_UP
from config import E8_ROLES, E7_ROLES,E6_ROLES,E5_ROLES,E4_ROLES
from config import E3_AND_UP,E2_AND_UP,E1_AND_UP
from config import E3_ROLES, E2_ROLES, E1_ROLES


def rank_to_roles(rank_str : str) -> list[int] | None:
    roles = None
    u_rank = rank_str.upper()
    if 'ADMIRALITY' in u_rank:
        roles = [BOA_ROLE]
    elif u_rank.startswith('E') and u_rank.endswith('+'):
        if   '8' in u_rank:
            roles = E8_AND_UP
        elif '7' in u_rank:
            roles = E7_AND_UP
        elif '6' in u_rank:
            roles = E6_AND_UP
        elif '5' in u_rank:
            roles = E5_AND_UP
        elif '4' in u_rank:
            roles = E4_AND_UP
        elif '3' in u_rank:
            roles = E3_AND_UP
        elif '2' in u_rank:
            roles = E2_AND_UP
        elif '1' in u_rank:
            roles = E1_AND_UP
    elif u_rank.startswith('E'):
        if   '8' in u_rank:
            roles = E8_ROLES
        elif '7' in u_rank:
            roles = E7_ROLES
        elif '6' in u_rank:
            roles = E6_ROLES
        elif '5' in u_rank:
            roles = E5_ROLES
        elif '4' in u_rank:
            roles = E4_ROLES
        elif '3' in u_rank:
            roles = E3_ROLES
        elif '2' in u_rank:
            roles = E2_ROLES
        elif '1' in u_rank:
            roles = E1_ROLES
    elif u_rank.startswith('O') and u_rank.endswith('+'):
        if   '8' in u_rank:
            roles = O8_AND_UP
        elif '7' in u_rank:
            roles = O7_AND_UP
        elif '6' in u_rank:
            roles = O6_AND_UP
        elif '5' in u_rank:
            roles = O5_AND_UP
        elif '4' in u_rank:
            roles = O4_AND_UP
        elif '3' in u_rank:
            roles = O3_AND_UP
        elif '2' in u_rank:
            roles = O2_AND_UP
        elif '1' in u_rank:
            roles = O1_AND_UP
    elif u_rank.startswith('O'):
        if   '8' in u_rank:
            roles = O8_ROLES
        elif '7' in u_rank:
            roles = O7_ROLES
        elif '6' in u_rank:
            roles = O6_ROLES
        elif '5' in u_rank:
            roles = O5_ROLES
        elif '4' in u_rank:
            roles = O4_ROLES
        elif '3' in u_rank:
            roles = O3_ROLES
        elif '2' in u_rank:
            roles = O2_ROLES
        elif '1' in u_rank:
            roles = O1_ROLES
    return roles
