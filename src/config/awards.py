from data.structs import Award, CombatAward, AwardsCollector

_AWARDS_THREAD_ID=1374118521927241779 

###############################################################################
## Medals And Ribbons - Voyage Medals
###############################################################################
_VOYAGE_EMBED_ID=1375472706237239317
CITATION_OF_VOAYGES = Award(
    threshold=5,
    ranks_responsible="E-6+",
    role_id=934090102735536188,
    embed_id=_VOYAGE_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
LEGION_OF_VOYAGES = Award(
    threshold=25,
    ranks_responsible="E-7+",
    role_id=983412707912998942,
    embed_id=_VOYAGE_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
HONORABLE_VOYAGER_MEDAL = Award(
    threshold=50,
    ranks_responsible="O-1+",
    role_id=1059271717836566588,
    embed_id=_VOYAGE_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
MERITORIOUS_VOYAGER_MEDAL = Award(
    threshold=100,
    ranks_responsible="O-4+",
    role_id=1059240151852797993,
    embed_id=_VOYAGE_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
ADMIRABLE_VOYAGER_MEDAL = Award(
    threshold=200,
    ranks_responsible="O-7+",
    role_id=1140637598457544857,
    embed_id=_VOYAGE_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
# Medals must be ordered lowest to highest voyage count
VOYAGE_MEDALS = (CITATION_OF_VOAYGES, LEGION_OF_VOYAGES, HONORABLE_VOYAGER_MEDAL, 
                 MERITORIOUS_VOYAGER_MEDAL, ADMIRABLE_VOYAGER_MEDAL)

###############################################################################
## Medals And Ribbons - Voyages Hosted Medals
###############################################################################
_HOSTED_EMBED_ID=1375472706237239317
SEA_SERVICE_RIBBON = Award(
    threshold=25,
    ranks_responsible="E-7+",
    role_id=1140740078025576569,
    embed_id=_HOSTED_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID,
)
MARITIME_SERVICE_MEDAL = Award(
    threshold=50,
    ranks_responsible="O-1+",
    role_id=1140740079808155688,
    embed_id=_HOSTED_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
LEGENDARY_SERVICE_MEDAL = Award(
    threshold=100,
    ranks_responsible="O-4+",
    role_id=1140740081594941460,
    embed_id=_HOSTED_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
ADMIRABLE_SERVICE_MEDAL = Award(
    threshold=200,
    ranks_responsible="O-7+",
    role_id=1205129048309637170,
    embed_id=_HOSTED_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)

# Medals must be ordered lowest to highest voyage count
HOSTED_MEDALS = (SEA_SERVICE_RIBBON, MARITIME_SERVICE_MEDAL,
                 LEGENDARY_SERVICE_MEDAL, ADMIRABLE_SERVICE_MEDAL)

###############################################################################
## Medals And Ribbons - Conduct Medals
###############################################################################
_CITATION_EMBED_ID=1375472616240054312
CITATION_OF_CONDUCT = Award(
    threshold=1, # This is not per se a threshold, but more an index of award importance
    ranks_responsible="E-6+",
    role_id=944648745503563806,
    embed_id=_CITATION_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
LEGION_OF_CONDUCT = Award(
    threshold=2,
    ranks_responsible="E-7+",
    role_id=1140739251739308042,
    embed_id=_CITATION_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
HONORABLE_CONDUCT = Award(
    threshold=3,
    ranks_responsible="O-1+",
    role_id=1140739253895180378,
    embed_id=_CITATION_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
MERITORIOUS_CONDUCT = Award(
    threshold=4,
    ranks_responsible="O-4+",
    role_id=1140739256214622329,
    embed_id=_CITATION_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
ADMIRABLE_CONDUCT = Award(
    threshold=5,
    ranks_responsible="O-7+",
    role_id=1140739259003850752,
    embed_id=_CITATION_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)

# Medals must be ordered lowest to highest in threshold
CONDUCT_MEDALS = (CITATION_OF_CONDUCT, LEGION_OF_CONDUCT, HONORABLE_CONDUCT,
                  MERITORIOUS_CONDUCT, ADMIRABLE_CONDUCT)

###############################################################################
## Medals And Ribbons - Combat Medals
###############################################################################
_COMBAT_EMBED_ID=1375472809110671402
CITATION_OF_COMBAT = CombatAward(
    threshold=2,
    streak=False,
    ranks_responsible="E-6+",
    role_id=944648920083079189,
    embed_id=_COMBAT_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
LEGION_OF_COMBAT = CombatAward(
    threshold=3,
    streak=True,
    ranks_responsible="E-7+",
    role_id=1140638151174541502,
    embed_id=_COMBAT_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
HONORABLE_COMBAT_ACTION = CombatAward(
    threshold=5,
    streak=True,
    ranks_responsible="O-1+",
    role_id=1140638148217544714,
    embed_id=_COMBAT_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
MERITORIOUS_COMBAT_ACTION = CombatAward(
    threshold=7,
    streak=True,
    ranks_responsible="O-4+",
    role_id=1140740442334433301,
    embed_id=_COMBAT_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
ADMIRABLE_COMBAT_ACTION = CombatAward(
    threshold=10,
    streak=True,
    ranks_responsible="O-7+",
    role_id=1140638153892450406,
    embed_id=_COMBAT_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)

# Medals must be ordered lowest to highest win streak
COMBAT_MEDALS = (CITATION_OF_COMBAT, LEGION_OF_COMBAT, HONORABLE_COMBAT_ACTION,
                 MERITORIOUS_COMBAT_ACTION, ADMIRABLE_COMBAT_ACTION)

###############################################################################
## Medals And Ribbons - Training and Recruiting
###############################################################################
_TRAINING_EMBED_ID=1375472904933871646
HONORABLE_TRAINING_RIBBON = Award(
    threshold=25,
    ranks_responsible="CO/XO of NRC or NETC",
    role_id=972552284145860619,
    embed_id=_TRAINING_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
MERITORIOUS_TRAINING_RIBBON = Award(
    threshold=50,
    ranks_responsible="CO/XO of NRC or NETC", 
    role_id=1205124628712792064,
    embed_id=_TRAINING_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
ADMIRABLE_TRAINING_RIBBON = Award(
    threshold=100,
    ranks_responsible="CO/XO of NRC or NETC",
    role_id=1205126555467255818,
    embed_id=_TRAINING_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)

# Medals must be ordered lowest to highest training count
TRAINING_MEDALS = (HONORABLE_TRAINING_RIBBON, MERITORIOUS_TRAINING_RIBBON, ADMIRABLE_TRAINING_RIBBON)

_RECRUIT_EMBED_ID=1375472904933871646
RECRUITMENT_RIBBON = Award(
    threshold=15,
    ranks_responsible="CO/XO of NRC",
    role_id=934071290875232267,
    embed_id=_RECRUIT_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)

# Medals must be ordered lowest to highest recruit count
RECRUIT_MEDALS = (RECRUITMENT_RIBBON,)


###############################################################################
## Medals And Ribbons - Attendance
###############################################################################
_ATTENDANCE_EMBED_ID=1375472904933871646
CITATION_OF_ATTENDANCE = Award(
    threshold=1,
    ranks_responsible="Head or XO of Scheduling Department",
    role_id=1286548679561445387,
    embed_id=_ATTENDANCE_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
LEGION_OF_ATTENDANCE = Award(
    threshold=2,
    ranks_responsible="Head or XO of Scheduling Department",
    role_id=1286548851028656178,
    embed_id=_ATTENDANCE_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
MERITORIOUS_ATTENDANCE_MEDAL = Award(
    threshold=4,
    ranks_responsible="Head or XO of Scheduling Department",
    role_id=1286548979235950602,
    embed_id=_ATTENDANCE_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
ADMIRABLE_ATTENDANCE_MEDAL = Award(
    threshold=6,
    ranks_responsible="Head or XO of Scheduling Department",
    role_id=1286549059288436757,
    embed_id=_ATTENDANCE_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)

# Medals must be ordered lowest to highest attendance count
ATTENDANCE_MEDALS = (CITATION_OF_ATTENDANCE, LEGION_OF_ATTENDANCE,
                     MERITORIOUS_ATTENDANCE_MEDAL, ADMIRABLE_ATTENDANCE_MEDAL)


###############################################################################
## Medals And Ribbons - Service Stripes
###############################################################################
_SERVICE_EMBED_ID=1375473002199646301
FOUR_MONTHS_SERVICE_STRIPES = Award(
    threshold=4,
    ranks_responsible="CO+",
    role_id=995304238773190667,
    embed_id=_SERVICE_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
SIX_MONTHS_SERVICE_STRIPES = Award(
    threshold=6,
    ranks_responsible="CO+",
    role_id=1083148237373964319,
    embed_id=_SERVICE_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
EIGHT_MONTHS_SERVICE_STRIPES = Award(
    threshold=8,
    ranks_responsible="CO+",
    role_id=1023358727358795786,
    embed_id=_SERVICE_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
TWELVE_MONTHS_SERVICE_STRIPES = Award(
    threshold=12,
    ranks_responsible="CO+",
    role_id=1066065470580609046,
    embed_id=_SERVICE_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
EIGHTEEN_MONTHS_SERVICE_STRIPES = Award(
    threshold=18,
    ranks_responsible="CO+",
    role_id=1202901182528364624,
    embed_id=_SERVICE_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)
TWNETYFOUR_MONTHS_SERVICE_STRIPES = Award(
    threshold=24,
    ranks_responsible="CO+",
    role_id=1204423843062485053,
    embed_id=_SERVICE_EMBED_ID,
    channelthread_id=_AWARDS_THREAD_ID
)

# Stripes must be ordered lowest to highest month count
SERVICE_STRIPES = (FOUR_MONTHS_SERVICE_STRIPES, SIX_MONTHS_SERVICE_STRIPES, EIGHT_MONTHS_SERVICE_STRIPES,
                   TWELVE_MONTHS_SERVICE_STRIPES, EIGHTEEN_MONTHS_SERVICE_STRIPES, TWNETYFOUR_MONTHS_SERVICE_STRIPES)

###############################################################################
## Medals And Ribbons - MISC
###############################################################################
NCO_IMPROVEMENT_RIBBON = Award(
    threshold=1,
    ranks_responsible="O-1+",
    role_id=995304090143838348,
    embed_id=1292514591854559263,
    channelthread_id=_AWARDS_THREAD_ID
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
    service=SERVICE_STRIPES
)

