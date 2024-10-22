from operator import index

from src.config.ranks_roles import RT_ROLES, DH_ROLES, E1_ROLES, E2_ROLES, E3_ROLES, VT_ROLES, E4_ROLES, E6_ROLES, \
    E8_ROLES, E7_ROLES, O1_ROLES, O3_ROLES, O4_ROLES, O5_ROLES, O6_ROLES, O8_ROLES, O7_ROLES
from src.data.structs import NavyRank, RankPrerequisites

DECKHAND = NavyRank(
    index=0,
    identifier="DH",
    role_ids=DH_ROLES,
    name="Deckhand",
    promotion_index={2} # Seaman
)
VETERAN = NavyRank(
    index=0,
    identifier="VT",
    role_ids=VT_ROLES,
    promotion_index={2} # Seaman
)
RETIRED = NavyRank(
    index=0,
    identifier="RT",
    role_ids=RT_ROLES,
    promotion_index={2} # Seaman
)
RECRUIT = NavyRank(
    index=1,
    identifier="E1",
    role_ids=E1_ROLES,
    name="Recruit",
    promotion_index={2} # Seaman
)
SEAMAN = NavyRank(
    index=2,
    identifier="E2",
    role_ids=E2_ROLES,
    name="Seaman",
    promotion_index={3} # Able Seaman
)
ABLE_SEAMAN = NavyRank(
    index=3,
    identifier="E3",
    role_ids=E3_ROLES,
    name="Able Seaman",
    promotion_index={4}, # Junior Petty Officer
    rank_prerequisites = RankPrerequisites(
        [
            "Decent activity in their squad chat."
        ]
    )
)
JUNIOR_PETTY_OFFICER = NavyRank(
    index=4,
    identifier="E4",
    role_ids=E4_ROLES,
    name="Junior Petty Officer",
    promotion_index={5}  # Petty Officer
)
PETTY_OFFICER = NavyRank(
    index=5,
    identifier="E6",
    role_ids=E6_ROLES,
    name="Petty Officer",
    promotion_index={6}  # Chief Petty Officer
)
CHIEF_PETTY_OFFICER = NavyRank(
    index=6,
    identifier="E7",
    role_ids=E7_ROLES,
    name="Chief Petty Officer",
    promotion_index={8,9}  # Senior Petty Officer / Midshipman
)
SENIOR_CHIEF_PETTY_OFFICER = NavyRank(
    index=8,
    identifier="E8",
    role_ids=E8_ROLES,
    name="Senior Petty Officer",
    promotion_index={9}  #  Midshipman
)
MIDSHIPMAN = NavyRank(
    index=9,
    identifier="O1",
    role_ids=O1_ROLES,
    name="Midshipman",
    promotion_index={10}  # Lieutenant
)
LIEUTENANT = NavyRank(
    index=10,
    identifier="O3",
    role_ids=O3_ROLES,
    name="Lieutenant",
    promotion_index={11} # Lieutenant Commander
)
LIEUTENANT_COMMANDER = NavyRank(
    index=11,
    identifier="O4",
    role_ids=O4_ROLES,
    name="Lieutenant Commander",
    promotion_index={12} # Commander
)
COMMANDER = NavyRank(
    index=12,
    identifier="O5",
    role_ids=O5_ROLES,
    name="Commander",
    promotion_index={13} # Captain
)
CAPTAIN = NavyRank(
    index=13,
    identifier="O6",
    role_ids=O6_ROLES,
    name="Captain",
    promotion_index={14} # Commodore
)
Commodore = NavyRank(
    index=15,
    identifier="O7",
    role_ids=O7_ROLES,
    name="Commodore",
    promotion_index={16} # Rear Admiral
)
REAR_ADMIRAL = NavyRank(
    index=16,
    identifier="O8",
    role_ids=O8_ROLES,
    name="Commodore",
)

RANKS = (
    DECKHAND,
    RECRUIT,
    RETIRED,
    SEAMAN,
    ABLE_SEAMAN,
    JUNIOR_PETTY_OFFICER,
    PETTY_OFFICER,
    CHIEF_PETTY_OFFICER,
    SENIOR_CHIEF_PETTY_OFFICER,
    MIDSHIPMAN,
    LIEUTENANT,
    LIEUTENANT_COMMANDER,
    COMMANDER,
    CAPTAIN,
    REAR_ADMIRAL
)