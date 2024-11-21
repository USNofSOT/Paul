from src.config.ships import SHIPS

###############################################################################
# USN SHIP ROLES
###############################################################################

ALL_SHIP_ROLES: list[int] = [
    ship.role_id for ship in SHIPS
]