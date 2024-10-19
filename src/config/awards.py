from data.structs import Award

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

MEDALS_AND_RIBBONS = {
    'voyages': VOYAGE_MEDALS,
}
