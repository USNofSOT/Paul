from __future__ import annotations

from data.structs import SubclassCollector

from src.data.repository.awards_repository import AwardsRepository

###############################################################################
## Roles - Cannoneer
###############################################################################
awards_repository = AwardsRepository()
ADEPT_CANNONEER = awards_repository.find_by_name("Adept Cannoneer")
PRO_CANNONEER = awards_repository.find_by_name("Pro Cannoneer")
MASTER_CANNONEER = awards_repository.find_by_name("Master Cannoneer")

# Subclass tiers must be ordered lowest to highest point count
CANNONEER_SUBCLASSES = (ADEPT_CANNONEER, PRO_CANNONEER, MASTER_CANNONEER)

###############################################################################
## Roles - Carpenter
###############################################################################
ADEPT_CARPENTER = awards_repository.find_by_name("Adept Carpenter")
PRO_CARPENTER = awards_repository.find_by_name("Pro Carpenter")
MASTER_CARPENTER = awards_repository.find_by_name("Master Carpenter")

# Subclass tiers must be ordered lowest to highest point count
CARPENTER_SUBCLASSES = (ADEPT_CARPENTER, PRO_CARPENTER, MASTER_CARPENTER)

###############################################################################
## Roles - Flex
###############################################################################
ADEPT_FLEX = awards_repository.find_by_name("Adept Flex")
PRO_FLEX = awards_repository.find_by_name("Pro Flex")
MASTER_FLEX = awards_repository.find_by_name("Master Flex")

# Subclass tiers must be ordered lowest to highest point count
FLEX_SUBCLASSES = (ADEPT_FLEX, PRO_FLEX, MASTER_FLEX)

###############################################################################
## Roles - Helm
###############################################################################
ADEPT_HELM = awards_repository.find_by_name("Adept Helm")
PRO_HELM = awards_repository.find_by_name("Pro Helm")
MASTER_HELM = awards_repository.find_by_name("Master Helm")

# Subclass tiers must be ordered lowest to highest point count
HELM_SUBCLASSES = (ADEPT_HELM, PRO_HELM, MASTER_HELM)

###############################################################################
## Grenadier
###############################################################################
GRENADIER = awards_repository.find_by_name("Grenadier")

# Subclass awards must be ordered lowest to highest point count
GRENADIER_SUBCLASSES = (GRENADIER,)

###############################################################################
## Field Surgeon
###############################################################################
FIELD_SURGEON = awards_repository.find_by_name("Field Surgeon")

# Subclass awards must be ordered lowest to highest point count
SURGEON_SUBCLASSES = (FIELD_SURGEON,)

###############################################################################
## Collector
###############################################################################
SUBCLASS_AWARDS = SubclassCollector(
    cannoneer=CANNONEER_SUBCLASSES,
    carpenter=CARPENTER_SUBCLASSES,
    flex=FLEX_SUBCLASSES,
    grenadier=GRENADIER_SUBCLASSES,
    helm=HELM_SUBCLASSES,
    surgeon=SURGEON_SUBCLASSES,
)
awards_repository.close_session()
