from src.config.ranks import LIEUTENANT, ADMIRAL_OF_THE_NAVY, CAPTAIN, COMMANDER, COMMODORE, JUNIOR_PETTY_OFFICER, \
    CHIEF_PETTY_OFFICER, ABLE_SEAMAN, LIEUTENANT_COMMANDER, PETTY_OFFICER, REAR_ADMIRAL, SENIOR_CHIEF_PETTY_OFFICER, \
    SEAMAN, RECRUIT, MIDSHIPMAN
from src.data.structs import RankAbbreviation, Abbreviation

###############################################################################
# Abbreviations - Rank abbreviations
###############################################################################

NAVY_ENLISTED_RANKS_ABBREVIATIONS = [
    RankAbbreviation(
        abbreviation="SR",
        meaning="Seaman Recruit",
        associated_rank=RECRUIT
    ),
    RankAbbreviation(
        abbreviation="SA",
        meaning="Seaman Apprentice"
    ),
    RankAbbreviation(
        abbreviation="SN",
        meaning="Seaman",
        associated_rank=SEAMAN
    ),
    RankAbbreviation(
        abbreviation="AS",
        meaning="Able Seaman",
        associated_rank=ABLE_SEAMAN
    ),
    RankAbbreviation(
        abbreviation="JPO",
        meaning="Junior Petty Officer",
        associated_rank=JUNIOR_PETTY_OFFICER
    ),
    RankAbbreviation(
        abbreviation="PO",
        meaning="Petty Officer",
        associated_rank=PETTY_OFFICER
    ),
    RankAbbreviation(
        abbreviation="CPO",
        meaning="Chief Petty Officer",
        associated_rank=CHIEF_PETTY_OFFICER
    ),
    RankAbbreviation(
        abbreviation="SCPO",
        meaning="Senior Chief Petty Officer",
        associated_rank=SENIOR_CHIEF_PETTY_OFFICER
    ),
    RankAbbreviation(
        abbreviation="MCPO",
        meaning="Master Chief Petty Officer",
    ),
    RankAbbreviation(
        abbreviation="MCPON",
        meaning="Master Chief Petty Officer of the Navy"
    )
]

MARINE_ENLISTED_RANKS_ABBREVIATIONS = [
    RankAbbreviation(
        abbreviation="LCPL",
        meaning="Lance Corporal",
        associated_rank=ABLE_SEAMAN
    ),
    RankAbbreviation(
        abbreviation="CPL",
        meaning="Corporal",
        associated_rank=JUNIOR_PETTY_OFFICER
    ),
    RankAbbreviation(
        abbreviation="SGT",
        meaning="Sergeant"
    ),
    RankAbbreviation(
        abbreviation="SSGT",
        meaning="Staff Sergeant",
        associated_rank=PETTY_OFFICER
    ),
    RankAbbreviation(
        abbreviation="GYSGT",
        meaning="Gunnery Sergeant",
        associated_rank=CHIEF_PETTY_OFFICER
    ),
    RankAbbreviation(
        abbreviation="MSGT",
        meaning="Master Sergeant",
        associated_rank=SENIOR_CHIEF_PETTY_OFFICER
    ),
    RankAbbreviation(
        abbreviation="SGTMAJ",
        meaning="Sergeant Major",
    ),
    RankAbbreviation(
        abbreviation="SMMC",
        meaning="Sergeant Major of the Marine Corps",

    )
]

NAVY_OFFICER_RANKS_ABBREVIATIONS = [
    RankAbbreviation(
        abbreviation="MIDN",
        meaning="Midshipmen",
        associated_rank=MIDSHIPMAN
    ),
    RankAbbreviation(
        abbreviation="LT",
        meaning="Lieutenant",
        associated_rank=LIEUTENANT
    ),
    RankAbbreviation(
        abbreviation="LCDR",
        meaning="Lieutenant Commander",
        associated_rank=LIEUTENANT_COMMANDER
    ),
    RankAbbreviation(
        abbreviation="CDR",
        meaning="Commander",
        associated_rank=COMMANDER
    ),
    RankAbbreviation(
        abbreviation="CAPT",
        meaning="Captain",
        associated_rank=CAPTAIN
    ),
    RankAbbreviation(
        abbreviation="CDRE",
        meaning="Commodore",
        associated_rank=COMMODORE
    ),
    RankAbbreviation(
        abbreviation="RADM",
        meaning="Rear Admiral",
        associated_rank=REAR_ADMIRAL
    ),
    RankAbbreviation(
        abbreviation="VADM",
        meaning="Vice Admiral"
    ),
    RankAbbreviation(
        abbreviation="ADM",
        meaning="Admiral"
    ),
    RankAbbreviation(
        abbreviation="AOTN",
        meaning="Admiral of the Navy",
        associated_rank=ADMIRAL_OF_THE_NAVY
    )
]

MARINE_OFFICER_RANKS_ABBREVIATIONS = [
    RankAbbreviation(
        abbreviation="2NDLT",
        meaning="2nd Lieutenant",
        associated_rank=MIDSHIPMAN
    ),
    RankAbbreviation(
        abbreviation="MCAPT",
        meaning="Marine Captain"
    ),
    RankAbbreviation(
        abbreviation="MAJ",
        meaning="Major",
        associated_rank=LIEUTENANT_COMMANDER
    ),
    RankAbbreviation(
        abbreviation="LTCOL",
        meaning="Lieutenant Colonel",
        associated_rank=COMMANDER
    ),
    RankAbbreviation(
        abbreviation="COL",
        meaning="Colonel",
        associated_rank=CAPTAIN
    ),
    RankAbbreviation(
        abbreviation="BRIG. GEN",
        meaning="Brigadier General",
        associated_rank=COMMODORE
    ),
    RankAbbreviation(
        abbreviation="MAJ. GEN",
        meaning="Major General",
    ),
    RankAbbreviation(
        abbreviation="LT. GEN",
        meaning="Lieutenant General",
    ),
    RankAbbreviation(
        abbreviation="GEN",
        meaning="General",
    )
]

RANK_ABBREVIATIONS = [
    *NAVY_ENLISTED_RANKS_ABBREVIATIONS,
    *MARINE_ENLISTED_RANKS_ABBREVIATIONS,
    *NAVY_OFFICER_RANKS_ABBREVIATIONS,
    *MARINE_OFFICER_RANKS_ABBREVIATIONS
]
###############################################################################
# Abbreviations - Miscellaneous abbreviations
###############################################################################

SPD_ABBREVIATIONS = [
    Abbreviation(
        abbreviation="SPD",
        meaning="Special Projects Division"
    ),
    Abbreviation(
        abbreviation="NETC",
        meaning="Naval Education and Training Command"
    ),
    Abbreviation(
        abbreviation="NRC",
        meaning="Navy Recruiting Command"
    ),
    Abbreviation(
        abbreviation="NSC",
        meaning="Navy Systems Command"
    )
]

MISC_ABBREVIATIONS = [
    Abbreviation(
        abbreviation="BOA",
        meaning="Board Of Admiralty"
    ),
    Abbreviation(
        abbreviation="CCC",
        meaning="Commander Challenge Coin"
    ),
    Abbreviation(
        abbreviation="COS",
        meaning="Chief of Ship"
    ),
    Abbreviation(
        abbreviation="CO",
        meaning="Commanding Officer"
    ),
    Abbreviation(
        abbreviation="HQ",
        meaning="Headquarters"
    ),
    Abbreviation(
        abbreviation="JE",
        meaning="Junior Enlisted"
    ),
    Abbreviation(
        abbreviation="NCO",
        meaning="Non-Commissioned Officer"
    ),
    Abbreviation(
        abbreviation="JLA",
        meaning="Junior Leadership Academy"
    ),
    Abbreviation(
        abbreviation="OTS",
        meaning="Officer Training School"
    ),
    Abbreviation(
        abbreviation="PORT",
        meaning="Left"
    ),
    Abbreviation(
        abbreviation="PVE",
        meaning="Player vs Environment"
    ),
    Abbreviation(
        abbreviation="PVP",
        meaning="Player vs Player"
    ),
    Abbreviation(
        abbreviation="SL",
        meaning="Squad Leader"
    ),
    Abbreviation(
        abbreviation="SNCO",
        meaning="Senior Non-Commissioned Officer"
    ),
    Abbreviation(
        abbreviation="SNLA",
        meaning="Senior Non-Commissioned Officer Leadership Academy"
    ),
    Abbreviation(
        abbreviation="STARBOARD",
        meaning="Right"
    ),
   Abbreviation(
        abbreviation="USN",
        meaning="United States Navy"
    ),
    Abbreviation(
        abbreviation="XO",
        meaning="Executive Officer"
    ),
    Abbreviation(
        abbreviation="COC",
        meaning="Chain Of Command"
    )
]

###############################################################################

ABBREVIATION_CATEGORIES = [ RANK_ABBREVIATIONS, SPD_ABBREVIATIONS, MISC_ABBREVIATIONS]
