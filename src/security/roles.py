from src.config.netc_server import HIGH_COMMAND_OF_NETC_ROLES
from src.config.ranks_roles import (
    JE_ROLE, NCO_ROLE, SNCO_ROLE, JO_ROLE, SO_ROLE, BOA_ROLE,
    NRC_ROLE, VT_ROLES, RT_ROLES, VOYAGE_PERMISSIONS, NSC_ROLE
)
from src.config.spd_servers import SPD_NSC_ROLE


class Role:
    JE = "JE"
    NCO = "NCO"
    SNCO = "SNCO"
    JO = "JO"
    SO = "SO"
    BOA = "BOA"

    # NSC Department
    NSC_OBSERVER = "NSC_OBSERVER"
    NSC_OPERATOR = "NSC_OPERATOR"
    NSC_ADMINISTRATOR = "NSC_ADMINISTRATOR"

    # Other Departments / Special
    NRC = "NRC"
    VETERAN = "VETERAN"
    RETIRED = "RETIRED"
    VOYAGE_PERMISSIONS = "VOYAGE_PERMISSIONS"
    NETC_HIGH_COMMAND = "NETC_HIGH_COMMAND"

DISCORD_ROLE_MAP = {
    JE_ROLE: Role.JE,
    NCO_ROLE: Role.NCO,
    SNCO_ROLE: Role.SNCO,
    JO_ROLE: Role.JO,
    SO_ROLE: Role.SO,
    BOA_ROLE: Role.BOA,
    NRC_ROLE: Role.NRC,
    VOYAGE_PERMISSIONS: Role.VOYAGE_PERMISSIONS,
    NSC_ROLE: Role.NSC_OBSERVER,
    SPD_NSC_ROLE: Role.NSC_OBSERVER,
}

# Add VT_ROLES (Veteran)
for role_id in VT_ROLES:
    DISCORD_ROLE_MAP[role_id] = Role.VETERAN

# Add RT_ROLES (Retired)
for role_id in RT_ROLES:
    DISCORD_ROLE_MAP[role_id] = Role.RETIRED

# Add NETC High Command
for role_id in HIGH_COMMAND_OF_NETC_ROLES:
    DISCORD_ROLE_MAP[role_id] = Role.NETC_HIGH_COMMAND
