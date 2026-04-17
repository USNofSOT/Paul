from .roles import Role

ROLE_HIERARCHY = {
    Role.BOA: [
        Role.SO, Role.JO, Role.SNCO, Role.NCO, Role.JE,
        Role.NSC_OPERATOR, Role.NSC_OBSERVER,
        Role.NRC, Role.NETC_HIGH_COMMAND
    ],
    Role.SO: [Role.JO, Role.SNCO, Role.NCO, Role.JE],
    Role.JO: [Role.SNCO, Role.NCO, Role.JE],
    Role.SNCO: [Role.NCO, Role.JE],
    Role.NCO: [Role.JE],

    # NSC Department Expansion
    Role.NSC_ADMINISTRATOR: [Role.NSC_OPERATOR, Role.NSC_OBSERVER],
    Role.NSC_OPERATOR: [Role.NSC_OBSERVER],
}
