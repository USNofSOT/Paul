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
    marine_name="Lance Corporal",
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
    marine_name="Corporal",
    promotion_index={5},  # Petty Officer
    rank_prerequisites = RankPrerequisites(
        [
            "Have 2FA enabled",
            "Write a minimum of 2 Logs on behalf of a Voyage Leader BEFORE beginning Day 1",
            "One of the logs will be a Patrol log",
            "No Warnings following E-3 Promotion",
            "Recommended by candidate's Squad Leader or above"
        ]
    )
)
PETTY_OFFICER = NavyRank(
    index=5,
    identifier="E6",
    role_ids=E6_ROLES,
    name="Petty Officer",
    marine_name="Staff Sergeant",
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
    marine_name="Gunnery Sergeant",
    promotion_index={8,9}, # Senior Petty Officer / Midshipman
    rank_prerequisites = RankPrerequisites(
        [
            "Interviewed for a SL position",
            "SNCO Board Passed",
            "Meets SNLA requirements"
        ]
    )
)
SENIOR_CHIEF_PETTY_OFFICER = NavyRank(
    index=8,
    identifier="E8",
    role_ids=E8_ROLES,
    name="Senior Petty Officer",
    marine_name="Master Sergeant",
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
    marine_name="Second Lieutenant",
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
    marine_name="Marine Captain",
    promotion_index={11}, # Lieutenant Commander
    rank_prerequisites=RankPrerequisites(
        [
            "Mentorship under an SO",
            "Meets OCS requirements"
        ]
    )
)
LIEUTENANT_COMMANDER = NavyRank(
    index=11,
    identifier="O4",
    role_ids=O4_ROLES,
    name="Lieutenant Commander",
    marine_name="Major",
    promotion_index={12}, # Commander
    rank_prerequisites=RankPrerequisites(
        [
            "Voted on by the BOA",
            "Meets SOCS requirements"
        ]
    )
)
COMMANDER = NavyRank(
    index=12,
    identifier="O5",
    role_ids=O5_ROLES,
    name="Commander",
    marine_name="Lieutenant Colonel",
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
    marine_name="Colonel",
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
    marine_name="Brigadier General",
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
    marine_name="Major General",
    promotion_index={16}, # Admiral Of The Navy
    rank_prerequisites=RankPrerequisites(
        [
            "Hand selected by the AOTN",
            "Has to give flag ship command to another SO"
        ]
    )
)
ADMIRAL_OF_THE_NAVY = NavyRank(
    index=16,
    identifier="AOTN",
    role_ids=AOTN_ROLES,
    promotion_index={101},
    name="Admiral Of The Navy"
)
DUNGEON_MASTER = NavyRank(
    index=101,
    identifier="DM",
    name="Dungeon Master"
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
    ADMIRAL_OF_THE_NAVY,
    DUNGEON_MASTER
)