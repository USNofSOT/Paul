from data.structs import Award, CombatAward, AwardsCollector

###############################################################################
## Medals And Ribbons - Voyage Medals
###############################################################################
_VOYAGE_EMBED_ID=1292514303936561183
CITATION_OF_VOAYGES = Award(
    role_id=934090102735536188,
    embed_id=_VOYAGE_EMBED_ID,
    ranks_responsible="E-6+",
    threshold=5
)
LEGION_OF_VOYAGES = Award(
    role_id=983412707912998942,
    embed_id=_VOYAGE_EMBED_ID,
    ranks_responsible="E-7+",
    threshold=25
)
HONORABLE_VOYAGER_MEDAL = Award(
    role_id=1059271717836566588,
    embed_id=_VOYAGE_EMBED_ID,
    ranks_responsible="O-1+",
    threshold=50
)
MERITORIOUS_VOYAGER_MEDAL = Award(
    role_id=1059240151852797993,
    embed_id=_VOYAGE_EMBED_ID,
    ranks_responsible="O-4+",
    threshold=100
)
ADMIRABLE_VOYAGER_MEDAL = Award(
    role_id=1140637598457544857,
    embed_id=_VOYAGE_EMBED_ID,
    ranks_responsible="O-7+",
    threshold=200
)
# Medals must be ordered lowest to highest voyage count
VOYAGE_MEDALS = (CITATION_OF_VOAYGES, LEGION_OF_VOYAGES, HONORABLE_VOYAGER_MEDAL, 
                 MERITORIOUS_VOYAGER_MEDAL, ADMIRABLE_VOYAGER_MEDAL)

###############################################################################
## Medals And Ribbons - Voyages Hosted Medals
###############################################################################
_HOSTED_EMBED_ID=1292514303936561183
SEA_SERVICE_RIBBON = Award(
    role_id=1140740078025576569,
    embed_id=_HOSTED_EMBED_ID,
    ranks_responsible="E-7+",
    threshold=25
)
MARITIME_SERVICE_MEDAL = Award(
    role_id=1140740079808155688,
    embed_id=_HOSTED_EMBED_ID,
    ranks_responsible="O-1+",
    threshold=50
)
LEGENDARY_SERVICE_MEDAL = Award(
    role_id=1140740081594941460,
    embed_id=_HOSTED_EMBED_ID,
    ranks_responsible="O-4+",
    threshold=100
)
ADMIRABLE_SERVICE_MEDAL = Award(
    role_id=1205129048309637170,
    embed_id=_HOSTED_EMBED_ID,
    ranks_responsible="O-7+",
    threshold=200
)

# Medals must be ordered lowest to highest voyage count
HOSTED_MEDALS = (SEA_SERVICE_RIBBON, MARITIME_SERVICE_MEDAL,
                 LEGENDARY_SERVICE_MEDAL, ADMIRABLE_SERVICE_MEDAL)

###############################################################################
## Medals And Ribbons - Combat Medals
###############################################################################
_COMBAT_EMBED_ID=1292514373751017586
CITATION_OF_COMBAT = CombatAward(
    role_id=944648920083079189,
    embed_id=_COMBAT_EMBED_ID,
    ranks_responsible="E-6+",
    threshold=2,
    streak=False
)
LEGION_OF_COMBAT = CombatAward(
    role_id=1140638151174541502,
    embed_id=_COMBAT_EMBED_ID,
    ranks_responsible="E-7+",
    threshold=3,
    streak=True
)
HONORABLE_COMBAT_ACTION = CombatAward(
    role_id=1140638148217544714,
    embed_id=_COMBAT_EMBED_ID,
    ranks_responsible="O-1+",
    threshold=5,
    streak=True
)
MERITORIOUS_COMBAT_ACTION = CombatAward(
    role_id=1140740442334433301,
    embed_id=_COMBAT_EMBED_ID,
    ranks_responsible="O-4+",
    threshold=7,
    streak=True
)
ADMIRABLE_COMBAT_ACTION = CombatAward(
    role_id=1140638153892450406,
    embed_id=_COMBAT_EMBED_ID,
    ranks_responsible="O-7+",
    threshold=10,
    streak=True
)

# Medals must be ordered lowest to highest win streak
COMBAT_MEDALS = (CITATION_OF_COMBAT, LEGION_OF_COMBAT, HONORABLE_COMBAT_ACTION,
                 MERITORIOUS_COMBAT_ACTION, ADMIRABLE_COMBAT_ACTION)

###############################################################################
## Medals And Ribbons - Training and Recruiting
###############################################################################
_TRAINING_EMBED_ID=1292514591854559263
HONORABLE_TRAINING_RIBBON = Award(
    role_id=972552284145860619,
    embed_id=_TRAINING_EMBED_ID,
    ranks_responsible="CO/XO of NRC or NETC",
    threshold=25
)
MERITORIOUS_TRAINING_RIBBON = Award(
    role_id=1205124628712792064,
    embed_id=_TRAINING_EMBED_ID,
    ranks_responsible="CO/XO of NRC or NETC", 
    threshold=50
)
ADMIRABLE_TRAINING_RIBBON = Award(
    role_id=1205126555467255818,
    embed_id=_TRAINING_EMBED_ID,
    ranks_responsible="CO/XO of NRC or NETC",
    threshold=100
)

# Medals must be ordered lowest to highest training count
TRAINING_MEDALS = (HONORABLE_TRAINING_RIBBON, MERITORIOUS_TRAINING_RIBBON, ADMIRABLE_TRAINING_RIBBON)

_RECRUIT_EMBED_ID=1292514591854559263
RECRUITMENT_RIBBON = Award(
    role_id=934071290875232267,
    embed_id=_RECRUIT_EMBED_ID,
    ranks_responsible="CO/XO of NRC",
    threshold=15
)

# Medals must be ordered lowest to highest recruit count
RECRUIT_MEDALS = (RECRUITMENT_RIBBON,)


###############################################################################
## Collector
###############################################################################
MEDALS_AND_RIBBONS = AwardsCollector(
    voyages=VOYAGE_MEDALS,
    hosted=HOSTED_MEDALS,
    combat=COMBAT_MEDALS,
    training=TRAINING_MEDALS,
    recruit=RECRUIT_MEDALS
)

