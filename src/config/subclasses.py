from data.structs import Award, SubclassCollector

_SUBCLASS_THREAD_ID=1292510408741228554
_SUBCLASS_EMBED_ID=1292522194492067954

_ADEPT_THRESHOLD=5
_PRO_THRESHOLD=15
_MASTER_THRESHOLD=25

_ADEPT_RANK="E-6+"
_PRO_RANK="E-6+"
_MASTER_RANK="E-6+"

###############################################################################
## Roles - Cannoneer
###############################################################################
_CANNONEER_EMBED_ID=_SUBCLASS_EMBED_ID
ADEPT_CANNONEER = Award(
    threshold=_ADEPT_THRESHOLD,
    ranks_responsible=_ADEPT_RANK,
    role_id=1145444479784980540,
    embed_id=_CANNONEER_EMBED_ID,
    channelthread_id=_SUBCLASS_THREAD_ID
)
PRO_CANNONEER = Award(
    threshold=_PRO_THRESHOLD,
    ranks_responsible=_PRO_RANK,
    role_id=1145444531060355266,
    embed_id=_CANNONEER_EMBED_ID,
    channelthread_id=_SUBCLASS_THREAD_ID
)
MASTER_CANNONEER = Award(
    threshold=_MASTER_THRESHOLD,
    ranks_responsible=_MASTER_RANK,
    role_id=1145444615198093425,
    embed_id=_CANNONEER_EMBED_ID,
    channelthread_id=_SUBCLASS_THREAD_ID
)

# Subclass tiers must be ordered lowest to highest point count
CANNONEER_SUBCLASSES = (ADEPT_CANNONEER, PRO_CANNONEER, MASTER_CANNONEER)

###############################################################################
## Roles - Carpenter
###############################################################################
_CARPENTER_EMBED_ID=_SUBCLASS_EMBED_ID
ADEPT_CARPENTER = Award(
    threshold=_ADEPT_THRESHOLD,
    ranks_responsible=_ADEPT_RANK,
    role_id=1145443782700048384,
    embed_id=_CARPENTER_EMBED_ID,
    channelthread_id=_SUBCLASS_THREAD_ID
)
PRO_CARPENTER = Award(
    threshold=_PRO_THRESHOLD,
    ranks_responsible=_PRO_RANK,
    role_id=1145443984156672070,
    embed_id=_CARPENTER_EMBED_ID,
    channelthread_id=_SUBCLASS_THREAD_ID
)
MASTER_CARPENTER = Award(
    threshold=_MASTER_THRESHOLD,
    ranks_responsible=_MASTER_RANK,
    role_id=1145444074170630187,
    embed_id=_CARPENTER_EMBED_ID,
    channelthread_id=_SUBCLASS_THREAD_ID
)

# Subclass tiers must be ordered lowest to highest point count
CARPENTER_SUBCLASSES = (ADEPT_CARPENTER, PRO_CARPENTER, MASTER_CARPENTER)

###############################################################################
## Roles - Flex
###############################################################################
_FLEX_EMBED_ID=_SUBCLASS_EMBED_ID
ADEPT_FLEX = Award(
    threshold=_ADEPT_THRESHOLD,
    ranks_responsible=_ADEPT_RANK,
    role_id=1145444124758130732,
    embed_id=_FLEX_EMBED_ID,
    channelthread_id=_SUBCLASS_THREAD_ID
)
PRO_FLEX = Award(
    threshold=_PRO_THRESHOLD,
    ranks_responsible=_PRO_RANK,
    role_id=1145444178164207727,
    embed_id=_FLEX_EMBED_ID,
    channelthread_id=_SUBCLASS_THREAD_ID
)
MASTER_FLEX = Award(
    threshold=_MASTER_THRESHOLD,
    ranks_responsible=_MASTER_RANK,
    role_id=1145444250411089962,
    embed_id=_FLEX_EMBED_ID,
    channelthread_id=_SUBCLASS_THREAD_ID
)

# Subclass tiers must be ordered lowest to highest point count
FLEX_SUBCLASSES = (ADEPT_FLEX, PRO_FLEX, MASTER_FLEX)

###############################################################################
## Roles - Helm
###############################################################################
_HELM_EMBED_ID=_SUBCLASS_EMBED_ID
ADEPT_HELM = Award(
    threshold=_ADEPT_THRESHOLD,
    ranks_responsible=_ADEPT_RANK,
    role_id=1145444308875477194,
    embed_id=_HELM_EMBED_ID,
    channelthread_id=_SUBCLASS_THREAD_ID
)
PRO_HELM = Award(
    threshold=_PRO_THRESHOLD,
    ranks_responsible=_PRO_RANK,
    role_id=1145444370825347122,
    embed_id=_HELM_EMBED_ID,
    channelthread_id=_SUBCLASS_THREAD_ID
)
MASTER_HELM = Award(
    threshold=_MASTER_THRESHOLD,
    ranks_responsible=_MASTER_RANK,
    role_id=1145444418892083210,
    embed_id=_HELM_EMBED_ID,
    channelthread_id=_SUBCLASS_THREAD_ID
)

# Subclass tiers must be ordered lowest to highest point count
HELM_SUBCLASSES = (ADEPT_HELM, PRO_HELM, MASTER_HELM)

###############################################################################
## Grenadier
###############################################################################
_GRENADIER_EMBED_ID=_SUBCLASS_EMBED_ID
GRENADIER = Award(
    threshold=10,
    ranks_responsible="E-6+",
    role_id=1143276410811727903,
    embed_id=_GRENADIER_EMBED_ID,
    channelthread_id=_SUBCLASS_THREAD_ID
)
# Subclass awards must be ordered lowest to highest point count
GRENADIER_SUBCLASSES = (GRENADIER,)

###############################################################################
## Field Surgeon
###############################################################################
_SURGEON_EMBED_ID=_SUBCLASS_EMBED_ID
FIELD_SURGEON = Award(
    threshold=5,
    ranks_responsible="E-6+",
    role_id=1143276412221014117,
    embed_id=_SURGEON_EMBED_ID,
    channelthread_id=_SUBCLASS_THREAD_ID
)
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
    surgeon=SURGEON_SUBCLASSES
)