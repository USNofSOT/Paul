from src.config.ranks_roles import (
    JE_ROLE, NCO_ROLE, SNCO_ROLE, JO_ROLE, SO_ROLE, BOA_ROLE
)


class Role:
    JE = "JE"
    NCO = "NCO"
    SNCO = "SNCO"
    JO = "JO"
    SO = "SO"
    BOA = "BOA"
    NSC_OBSERVER = "NSC_OBSERVER"
    NSC_OPERATOR = "NSC_OPERATOR"
    NSC_ADMINISTRATOR = "NSC_ADMINISTRATOR"


DISCORD_ROLE_MAP = {
    JE_ROLE: Role.JE,
    NCO_ROLE: Role.NCO,
    SNCO_ROLE: Role.SNCO,
    JO_ROLE: Role.JO,
    SO_ROLE: Role.SO,
    BOA_ROLE: Role.BOA,
}
