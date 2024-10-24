from src.config.ranks import LIEUTENANT, ADMIRAL_OF_THE_NAVY, CAPTAIN, COMMANDER, COMMODORE, JUNIOR_PETTY_OFFICER, \
    CHIEF_PETTY_OFFICER, ABLE_SEAMAN, LIEUTENANT_COMMANDER, PETTY_OFFICER, REAR_ADMIRAL, SENIOR_CHIEF_PETTY_OFFICER, \
    SEAMAN, RECRUIT
from src.data.structs import RankAbbreviation, Abbreviation

###############################################################################
# Abbreviations - Rank abbreviations
###############################################################################
ABBREVIATION_LIEUTENANT = RankAbbreviation(
    abbreviation="LT",
    meaning="Lieutenant",
    associated_rank=LIEUTENANT
)
ABBREVIATION_ADMIRAL = RankAbbreviation(
    abbreviation="ADM",
    meaning="Admiral"
)
ABBREVIATION_ADMIRAL_OF_THE_NAVY = RankAbbreviation(
    abbreviation="AOTN",
    meaning="Admiral of the Navy",
    associated_rank=ADMIRAL_OF_THE_NAVY
)
ABBREVIATION_BRIGADIER_GENERAL = RankAbbreviation(
    abbreviation="BRIG. GEN",
    meaning="Brigadier General",
    associated_rank=COMMODORE
)
ABBREVIATION_CAPTAIN_NAVY = RankAbbreviation(
    abbreviation="CAPT",
    meaning="Captain (NAVY)",
    associated_rank=CAPTAIN
)
ABBREVIATION_COMMANDER = RankAbbreviation(
    abbreviation="CDR",
    meaning="Commander",
    associated_rank=COMMANDER
)
ABBREVIATION_COLONEL = RankAbbreviation(
    abbreviation="COL",
    meaning="Colonel",
    associated_rank=CAPTAIN
)
ABBREVIATION_COMMODORE = RankAbbreviation(
    abbreviation="COM",
    meaning="Commodore",
    associated_rank=COMMODORE
)
ABBREVIATION_CORPORAL = RankAbbreviation(
    abbreviation="CPL",
    meaning="Corporal",
    associated_rank=JUNIOR_PETTY_OFFICER
)
ABBREVIATION_CHIEF_PETTY_OFFICER = RankAbbreviation(
    abbreviation="CPO",
    meaning="Chief Petty Officer",
    associated_rank=CHIEF_PETTY_OFFICER
)
ABBREVIATION_MARINE_CAPTAIN = RankAbbreviation(
    abbreviation="MCAPT",
    meaning="Marine Captain",
    associated_rank=LIEUTENANT
)
ABBREVIATION_LANCE_CORPORAL = RankAbbreviation(
    abbreviation="LCPL",
    meaning="Lance Corporal",
    associated_rank=ABLE_SEAMAN
)
ABBREVIATION_LIEUTENANT_COLONEL = RankAbbreviation(
    abbreviation="LT. COL",
    meaning="Lieutenant Colonel",
    associated_rank=COMMANDER
)
ABBREVIATION_LIEUTENANT_COMMANDER = RankAbbreviation(
    abbreviation="LCDR",
    meaning="Lieutenant Commander",
    associated_rank=LIEUTENANT_COMMANDER
)
ABBREVIATION_MAJOR_GENERAL = RankAbbreviation(
    abbreviation="MAJ. GEN",
    meaning="Major General"
)
ABBREVIATION_MAJOR = RankAbbreviation(
    abbreviation="MAJ",
    meaning="Major",
    associated_rank=LIEUTENANT_COMMANDER
)
ABBREVIATION_MASTER_CHIEF_PETTY_OFFICER = RankAbbreviation(
    abbreviation="MCPO",
    meaning="Master Chief Petty Officer",
)
ABBREVIATION_MASTER_CHIEF_PETTY_OFFICER_OF_THE_NAVY = RankAbbreviation(
    abbreviation="MCPON",
    meaning="Master Chief Petty Officer of the Navy"
)
ABBREVIATION_PETTY_OFFICER = RankAbbreviation(
    abbreviation="PO",
    meaning="Petty Officer",
    associated_rank=PETTY_OFFICER
)
ABBREVIATION_REAR_ADMIRAL = RankAbbreviation(
    abbreviation="RADM",
    meaning="Rear Admiral",
    associated_rank=REAR_ADMIRAL
)
ABBREVIATION_SEAMAN_APPRENTICE = RankAbbreviation(
    abbreviation="SA",
    meaning="Seaman Apprentice"
)
ABBREVIATION_SENIOR_CHIEF_PETTY_OFFICER = RankAbbreviation(
    abbreviation="SCPO",
    meaning="Senior Chief Petty Officer",
    associated_rank=SENIOR_CHIEF_PETTY_OFFICER
)
ABBREVIATION_SERGEANT = RankAbbreviation(
    abbreviation="SGT",
    meaning="Sergeant"
)
ABBREVIATION_SEAMAN = RankAbbreviation(
    abbreviation="SN",
    meaning="Seaman",
    associated_rank=SEAMAN
)
ABBREVIATION_SEAMAN_RECRUIT = RankAbbreviation(
    abbreviation="SR",
    meaning="Seaman Recruit",
    associated_rank=RECRUIT
)
ABBREVIATION_VICE_ADMIRAL = RankAbbreviation(
    abbreviation="VADM",
    meaning="Vice Admiral",
)

RANK_ABBREVIATIONS = [
    ABBREVIATION_LIEUTENANT,
    ABBREVIATION_ADMIRAL,
    ABBREVIATION_ADMIRAL_OF_THE_NAVY,
    ABBREVIATION_BRIGADIER_GENERAL,
    ABBREVIATION_CAPTAIN_NAVY,
    ABBREVIATION_COMMANDER,
    ABBREVIATION_COLONEL,
    ABBREVIATION_COMMODORE,
    ABBREVIATION_CORPORAL,
    ABBREVIATION_CHIEF_PETTY_OFFICER,
    ABBREVIATION_MARINE_CAPTAIN,
    ABBREVIATION_LANCE_CORPORAL,
    ABBREVIATION_LIEUTENANT_COLONEL,
    ABBREVIATION_LIEUTENANT_COMMANDER,
    ABBREVIATION_MAJOR_GENERAL,
    ABBREVIATION_MAJOR,
    ABBREVIATION_MASTER_CHIEF_PETTY_OFFICER,
    ABBREVIATION_MASTER_CHIEF_PETTY_OFFICER_OF_THE_NAVY,
    ABBREVIATION_PETTY_OFFICER,
    ABBREVIATION_REAR_ADMIRAL,
    ABBREVIATION_SEAMAN_APPRENTICE,
    ABBREVIATION_SENIOR_CHIEF_PETTY_OFFICER,
    ABBREVIATION_SERGEANT,
    ABBREVIATION_SEAMAN,
    ABBREVIATION_SEAMAN_RECRUIT,
    ABBREVIATION_VICE_ADMIRAL,
]
###############################################################################
# Abbreviations - Miscellaneous abbreviations
###############################################################################

ABBREVIATION_BOARD_OF_ADMIRALTY = Abbreviation(
    abbreviation="BOA",
    meaning="Board Of Admiralty"
)
ABBREVIATION_COMMANDER_CHALLENGE_COIN = Abbreviation(
    abbreviation="CCC",
    meaning="Commander Challenge Coin"
)
ABBREVIATION_CHIEF_OF_SHIP = Abbreviation(
    abbreviation="COS",
    meaning="Chief of Ship"
)
ABBREVIATION_COMMANDING_OFFICER = Abbreviation(
    abbreviation="CO",
    meaning="Commanding Officer"
)
ABBREVIATION_HEADQUARTERS = Abbreviation(
    abbreviation="HQ",
    meaning="Headquarters"
)
ABBREVIATION_JUNIOR_ENLISTED = Abbreviation(
    abbreviation="JE",
    meaning="Junior Enlisted"
)
ABBREVIATION_NON_COMMISSIONED_OFFICER = Abbreviation(
    abbreviation="NCO",
    meaning="Non-Commissioned Officer"
)
ABBREVIATION_JUNIOR_LEADERSHIP_ACADEMY = Abbreviation(
    abbreviation="JLA",
    meaning="Junior Leadership Academy"
)
ABBREVIATION_OFFICER_TRAINING_SCHOOL = Abbreviation(
    abbreviation="OTS",
    meaning="Officer Training School"
)
ABBREVIATION_PORT = Abbreviation(
    abbreviation="PORT",
    meaning="Left"
)
ABBREVIATION_PLAYER_VS_ENEMY = Abbreviation(
    abbreviation="PVE",
    meaning="Player vs Enemy"
)
ABBREVIATION_PLAYER_VS_PLAYER = Abbreviation(
    abbreviation="PVP",
    meaning="Player vs Player"
)
ABBREVIATION_SQUAD_LEADER = Abbreviation(
    abbreviation="SL",
    meaning="Squad Leader"
)
ABBREVIATION_SENIOR_NON_COMMISSIONED_OFFICER = Abbreviation(
    abbreviation="SNCO",
    meaning="Senior Non-Commissioned Officer"
)
ABBREVIATION_SENIOR_NON_COMMISSIONED_OFFICER_LEADERSHIP_ACADEMY = Abbreviation(
    abbreviation="SNLA",
    meaning="Senior Non-Commissioned Officer Leadership Academy"
)
ABBREVIATION_SPECIAL_PROJECTS_DIVISION = Abbreviation(
    abbreviation="SPD",
    meaning="Special Projects Division"
)
ABBREVIATION_STARBOARD = Abbreviation(
    abbreviation="STARBOARD",
    meaning="Right"
)
ABBREVIATION_UNITED_STATES_NAVY = Abbreviation(
    abbreviation="USN",
    meaning="United States Navy"
)
ABBREVIATION_EXECUTIVE_OFFICER = Abbreviation(
    abbreviation="XO",
    meaning="Executive Officer"
)
ABBREVIATION_NAVAL_EDUCATION_AND_TRAINING_COMMAND = Abbreviation(
    abbreviation="NETC",
    meaning="Naval Education and Training Command"
)
ABBREVIATION_NEW_RECRUIT_COMMAND_DEPARTMENT = Abbreviation(
    abbreviation="NRC",
    meaning="New Recruit Command Department"
)

MISC_ABBREVIATIONS = [
    ABBREVIATION_BOARD_OF_ADMIRALTY,
    ABBREVIATION_COMMANDER_CHALLENGE_COIN,
    ABBREVIATION_CHIEF_OF_SHIP,
    ABBREVIATION_COMMANDING_OFFICER,
    ABBREVIATION_HEADQUARTERS,
    ABBREVIATION_JUNIOR_ENLISTED,
    ABBREVIATION_NON_COMMISSIONED_OFFICER,
    ABBREVIATION_JUNIOR_LEADERSHIP_ACADEMY,
    ABBREVIATION_OFFICER_TRAINING_SCHOOL,
    ABBREVIATION_PORT,
    ABBREVIATION_PLAYER_VS_ENEMY,
    ABBREVIATION_PLAYER_VS_PLAYER,
    ABBREVIATION_SQUAD_LEADER,
    ABBREVIATION_SENIOR_NON_COMMISSIONED_OFFICER,
    ABBREVIATION_SENIOR_NON_COMMISSIONED_OFFICER_LEADERSHIP_ACADEMY,
    ABBREVIATION_SPECIAL_PROJECTS_DIVISION,
    ABBREVIATION_STARBOARD,
    ABBREVIATION_UNITED_STATES_NAVY,
    ABBREVIATION_EXECUTIVE_OFFICER,
    ABBREVIATION_NAVAL_EDUCATION_AND_TRAINING_COMMAND,
    ABBREVIATION_NEW_RECRUIT_COMMAND_DEPARTMENT,
]

###############################################################################

ABBREVIATION_CATEGORIES = [ RANK_ABBREVIATIONS, MISC_ABBREVIATIONS ]