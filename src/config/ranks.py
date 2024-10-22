from src.config.ranks_roles import RT_ROLES, DH_ROLES, E1_ROLES, E2_ROLES, E3_ROLES, VT_ROLES, E4_ROLES, E6_ROLES, \
    E8_ROLES, E7_ROLES, O1_ROLES, O3_ROLES, O4_ROLES, O5_ROLES, O6_ROLES, O8_ROLES, O7_ROLES, AOTN_ROLES
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
    name="Veteran",
    promotion_index={2} # Seaman
)
RETIRED = NavyRank(
    index=0,
    identifier="RT",
    role_ids=RT_ROLES,
    name="Retired",
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
    promotion_index={5},  # Petty Officer
    rank_prerequisites = RankPrerequisites(
        [
            "Have 2FA enabled"
        ]
    )
)
PETTY_OFFICER = NavyRank(
    index=5,
    identifier="E6",
    role_ids=E6_ROLES,
    name="Petty Officer",
    promotion_index={6},  # Chief Petty Officer
    rank_prerequisites = RankPrerequisites(
        [
            "Applying for a position of XO to a squad or becoming a squad leader (when available)"
        ]
    )
)
CHIEF_PETTY_OFFICER = NavyRank(
    index=6,
    identifier="E7",
    role_ids=E7_ROLES,
    name="Chief Petty Officer",
    promotion_index={8,9}, # Senior Petty Officer / Midshipman
    rank_prerequisites = RankPrerequisites(
        [
            "Interviewed for a SL position",
            "SNCO Board Passed"
        ]
    )
)
SENIOR_CHIEF_PETTY_OFFICER = NavyRank(
    index=8,
    identifier="E8",
    role_ids=E8_ROLES,
    name="Senior Petty Officer",
    promotion_index={9}, #  Midshipman
    rank_prerequisites=RankPrerequisites(
        [
            "Interviewed for a CoS position"
        ]
    )
)
MIDSHIPMAN = NavyRank(
    index=9,
    identifier="O1",
    role_ids=O1_ROLES,
    name="Midshipman",
    promotion_index={10},  # Lieutenant
    rank_prerequisites=RankPrerequisites(
        [
            "Officer Board"
        ]
    )
)
LIEUTENANT = NavyRank(
    index=10,
    identifier="O3",
    role_ids=O3_ROLES,
    name="Lieutenant",
    promotion_index={11}, # Lieutenant Commander
    rank_prerequisites=RankPrerequisites(
        [
            "Mentorship under an SO"
        ]
    )
)
LIEUTENANT_COMMANDER = NavyRank(
    index=11,
    identifier="O4",
    role_ids=O4_ROLES,
    name="Lieutenant Commander",
    promotion_index={12}, # Commander
    rank_prerequisites=RankPrerequisites(
        [
            "Voted on by the BOA"
        ]
    )
)
COMMANDER = NavyRank(
    index=12,
    identifier="O5",
    role_ids=O5_ROLES,
    name="Commander",
    promotion_index={13}, # Captain
    rank_prerequisites=RankPrerequisites(
        [
            "Recruit and maintain 4 members from outside the server on your ship, not including CO/XO/COS",
            "Functional CoC on their ship (Can fulfill all of it's ship duties despite being incomplete)"
        ]
    )
)
CAPTAIN = NavyRank(
    index=13,
    identifier="O6",
    role_ids=O6_ROLES,
    name="Captain",
    promotion_index={14}, # Commodore
    rank_prerequisites = RankPrerequisites(
        [
            "Very Active ship",
            "Full CoC on their ship (CoS is optional)"
        ]
    )
)
COMMODORE = NavyRank(
    index=14,
    identifier="O7",
    role_ids=O7_ROLES,
    name="Commodore",
    promotion_index={15}, # Rear Admiral
    rank_prerequisites=RankPrerequisites(
        [
            "Hand selected by the AOTN"
        ]
    )
)
REAR_ADMIRAL = NavyRank(
    index=15,
    identifier="O8",
    role_ids=O8_ROLES,
    name="Rear Admiral",
    rank_prerequisites=RankPrerequisites(
        [
            "Hand selected by the AOTN"
        ]
    )
)
ADMIRAL_OF_THE_NAVY = NavyRank(
    index=100,
    identifier="GOD",
    role_ids=AOTN_ROLES,
    name="Admiral Of The Navy"
)

RANKS = (
    DECKHAND,
    RECRUIT,
    RETIRED,
    VETERAN,
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
    COMMODORE,
    REAR_ADMIRAL,
    ADMIRAL_OF_THE_NAVY
)