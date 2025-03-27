from data.repository.awards_repository import AwardsRepository
from data.structs import Award, AwardsCollector

awards_repository = AwardsRepository()

_AWARDS_THREAD_ID = 1292510151219347519

###############################################################################
## Medals And Ribbons - Voyage Medals
###############################################################################
CITATION_OF_VOAYGES = awards_repository.find_by_name("Citation of Voyages")
LEGION_OF_VOYAGES = awards_repository.find_by_name("Legion of Voyages")
HONORABLE_VOYAGER_MEDAL = awards_repository.find_by_name("Honorable Voyager Medal")
MERITORIOUS_VOYAGER_MEDAL = awards_repository.find_by_name("Meritorious Voyager Medal")
ADMIRABLE_VOYAGER_MEDAL = awards_repository.find_by_name("Admirable Voyager Medal")

# Medals must be ordered lowest to highest voyage count
VOYAGE_MEDALS = (
    CITATION_OF_VOAYGES,
    LEGION_OF_VOYAGES,
    HONORABLE_VOYAGER_MEDAL,
    MERITORIOUS_VOYAGER_MEDAL,
    ADMIRABLE_VOYAGER_MEDAL,
)

###############################################################################
## Medals And Ribbons - Voyages Hosted Medals
###############################################################################
_HOSTED_EMBED_ID = 1292514303936561183
SEA_SERVICE_RIBBON = awards_repository.find_by_name("Sea Service Ribbon")
MARITIME_SERVICE_MEDAL = awards_repository.find_by_name("Maritime Service Medal")
LEGENDARY_SERVICE_MEDAL = awards_repository.find_by_name("Legendary Service Medal")
ADMIRABLE_SERVICE_MEDAL = awards_repository.find_by_name("Admirable Service Medal")

# Medals must be ordered lowest to highest voyage count
HOSTED_MEDALS = (
    SEA_SERVICE_RIBBON,
    MARITIME_SERVICE_MEDAL,
    LEGENDARY_SERVICE_MEDAL,
    ADMIRABLE_SERVICE_MEDAL,
)

###############################################################################
## Medals And Ribbons - Conduct Medals
###############################################################################
_CITATION_EMBED_ID = 1292514180208787519
CITATION_OF_CONDUCT = awards_repository.find_by_name("Citation of Conduct")
LEGION_OF_CONDUCT = awards_repository.find_by_name("Legion of Conduct")
HONORABLE_CONDUCT = awards_repository.find_by_name("Honorable Conduct Medal")
MERITORIOUS_CONDUCT = awards_repository.find_by_name("Meritorious Conduct Medal")
ADMIRABLE_CONDUCT = awards_repository.find_by_name("Admirable Conduct Medal")

# Medals must be ordered lowest to highest in threshold
CONDUCT_MEDALS = (
    CITATION_OF_CONDUCT,
    LEGION_OF_CONDUCT,
    HONORABLE_CONDUCT,
    MERITORIOUS_CONDUCT,
    ADMIRABLE_CONDUCT,
)

###############################################################################
## Medals And Ribbons - Combat Medals
###############################################################################
_COMBAT_EMBED_ID = 1292514373751017586
CITATION_OF_COMBAT = awards_repository.find_by_name("Citation of Combat")
LEGION_OF_COMBAT = awards_repository.find_by_name("Legion of Combat")
HONORABLE_COMBAT_ACTION = awards_repository.find_by_name("Honorable Combat Action")
MERITORIOUS_COMBAT_ACTION = awards_repository.find_by_name("Meritorious Combat Action")
ADMIRABLE_COMBAT_ACTION = awards_repository.find_by_name("Admirable Combat Action")

# Medals must be ordered lowest to highest win streak
COMBAT_MEDALS = (
    CITATION_OF_COMBAT,
    LEGION_OF_COMBAT,
    HONORABLE_COMBAT_ACTION,
    MERITORIOUS_COMBAT_ACTION,
    ADMIRABLE_COMBAT_ACTION,
)

###############################################################################
## Medals And Ribbons - Training and Recruiting
###############################################################################
HONORABLE_TRAINING_RIBBON = awards_repository.find_by_name("Honorable Training Ribbon")
MERITORIOUS_TRAINING_RIBBON = awards_repository.find_by_name(
    "Meritorious Training Ribbon"
)
ADMIRABLE_TRAINING_RIBBON = awards_repository.find_by_name("Admirable Training Ribbon")

# Medals must be ordered lowest to highest training count
TRAINING_MEDALS = (
    HONORABLE_TRAINING_RIBBON,
    MERITORIOUS_TRAINING_RIBBON,
    ADMIRABLE_TRAINING_RIBBON,
)

_RECRUIT_EMBED_ID = 1292514591854559263
RECRUITMENT_RIBBON = Award(
    threshold=15,
    ranks_responsible="CO/XO of NRC",
    role_id=934071290875232267,
    embed_id=_RECRUIT_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID,
)

# Medals must be ordered lowest to highest recruit count
RECRUIT_MEDALS = (RECRUITMENT_RIBBON,)


###############################################################################
## Medals And Ribbons - Attendance
###############################################################################
_ATTENDANCE_EMBED_ID = 1292514591854559263
CITATION_OF_ATTENDANCE = awards_repository.find_by_name("Citation of Attendance")
LEGION_OF_ATTENDANCE = awards_repository.find_by_name("Legion of Attendance")
MERITORIOUS_ATTENDANCE_MEDAL = awards_repository.find_by_name(
    "Meritorious Attendance Medal"
)
ADMIRABLE_ATTENDANCE_MEDAL = awards_repository.find_by_name(
    "Admirable Attendance Medal"
)

# Medals must be ordered lowest to highest attendance count
ATTENDANCE_MEDALS = (
    CITATION_OF_ATTENDANCE,
    LEGION_OF_ATTENDANCE,
    MERITORIOUS_ATTENDANCE_MEDAL,
    ADMIRABLE_ATTENDANCE_MEDAL,
)


###############################################################################
## Medals And Ribbons - Service Stripes
###############################################################################

FOUR_MONTHS_SERVICE_STRIPES = awards_repository.find_by_name(
    "Four Months Service Stripes"
)
SIX_MONTHS_SERVICE_STRIPES = awards_repository.find_by_name(
    "Six Months Service Stripes"
)
EIGHT_MONTHS_SERVICE_STRIPES = awards_repository.find_by_name(
    "Eight Months Service Stripes"
)
TWELVE_MONTHS_SERVICE_STRIPES = awards_repository.find_by_name(
    "Twelve Months Service Stripes"
)
EIGHTEEN_MONTHS_SERVICE_STRIPES = awards_repository.find_by_name(
    "Eighteen Months Service Stripes"
)
TWNETYFOUR_MONTHS_SERVICE_STRIPES = awards_repository.find_by_name(
    "Twenty-Four Months Service Stripes"
)

# Stripes must be ordered lowest to highest month count
SERVICE_STRIPES = (
    FOUR_MONTHS_SERVICE_STRIPES,
    SIX_MONTHS_SERVICE_STRIPES,
    EIGHT_MONTHS_SERVICE_STRIPES,
    TWELVE_MONTHS_SERVICE_STRIPES,
    EIGHTEEN_MONTHS_SERVICE_STRIPES,
    TWNETYFOUR_MONTHS_SERVICE_STRIPES,
)

###############################################################################
## Medals And Ribbons - MISC
###############################################################################
NCO_IMPROVEMENT_RIBBON = Award(
    threshold=1,
    ranks_responsible="O-1+",
    role_id=995304090143838348,
    embed_id=1292514591854559263,
    channelthread_id=_AWARDS_THREAD_ID,
)

###############################################################################
## Collector
###############################################################################
MEDALS_AND_RIBBONS = AwardsCollector(
    voyages=VOYAGE_MEDALS,
    hosted=HOSTED_MEDALS,
    combat=COMBAT_MEDALS,
    training=TRAINING_MEDALS,
    recruit=RECRUIT_MEDALS,
    attendance=ATTENDANCE_MEDALS,
    service=SERVICE_STRIPES,
)
