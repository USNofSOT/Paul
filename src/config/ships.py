from src.config.main_server import (
    BC_GLETSJER,
    BC_ADUN,
    BC_ARIZONA,
    BC_HYPERION,
    BC_LUSTY,
    BC_SERENITY,
    BC_PHANTOM,
    BC_NIGHTINGALE,
    BC_SILVERCLAW,
    BC_TITAN,
    BC_BERSERKER,
    BC_VENOM,
)
from src.data.structs import Ship

ROLE_ID_LUSTY = 933919139700019222
ROLE_ID_BERSERKER = 1164671319338664007
ROLE_ID_SERENITY = 1002303636522680391
ROLE_ID_ADUN = 1242143582463332402
ROLE_ID_GLETSJER = 1084451910578339880
ROLE_ID_HYPERION = 1157426517912076318
ROLE_ID_NIGHTINGALE = 967531117882261536
ROLE_ID_ARIZONA = 1058840733248933908
ROLE_ID_PHANTOM = 1274251672876617792
ROLE_ID_SILVERCLAW = 977935623774162954
ROLE_ID_VENOM = 1237838106711822457
ROLE_ID_TITAN = 1247405133130764329

SIZE_2_SQUADS = 24
SIZE_3_SQUADS = 33

###############################################################################
# Ships - Ship objects
###############################################################################
SHIPS = [
    Ship(
        name="USS Illustrious",
        boat_command_channel_id=BC_LUSTY,
        role_id=ROLE_ID_LUSTY,
        emoji="<:Lusty:1079841997021524018>",
        size=SIZE_2_SQUADS,
    ),
    Ship(
        name="USS Berserker",
        boat_command_channel_id=BC_BERSERKER,
        role_id=ROLE_ID_BERSERKER,
        emoji="<:Berserker:1390427238922719275>",
        size=SIZE_2_SQUADS,
    ),
    Ship(
        name="USS Serenity",
        boat_command_channel_id=BC_SERENITY,
        role_id=ROLE_ID_SERENITY,
        emoji="<:Serenity:1356016930032713879>",
        size=SIZE_2_SQUADS,
    ),
    Ship(
        name="USS Adun",
        boat_command_channel_id=BC_ADUN,
        role_id=ROLE_ID_ADUN,
        emoji="<:Adun:1251266293601013871>",
        size=SIZE_3_SQUADS
    ),
    Ship(
        name="USS Gletsjer",
        boat_command_channel_id=BC_GLETSJER,
        role_id=ROLE_ID_GLETSJER,
        emoji="<:Gletsjer:1356717285171265818>",
        size=SIZE_2_SQUADS,
    ),
    Ship(
        name="USS Hyperion",
        boat_command_channel_id=BC_HYPERION,
        role_id=ROLE_ID_HYPERION,
        emoji="<:hyperion1:1162043891185369199>",
        size=SIZE_3_SQUADS,
    ),
    Ship(
        name="USS Nightingale",
        boat_command_channel_id=BC_NIGHTINGALE,
        role_id=ROLE_ID_NIGHTINGALE,
        emoji="<:nightingale:1382145592934924370>",
        size=SIZE_3_SQUADS,
    ),
    Ship(
        name="USS Defiant",
        boat_command_channel_id=BC_ARIZONA,
        role_id=ROLE_ID_ARIZONA,
        emoji="<:Defiant:1354503521747075072>",
        size=SIZE_3_SQUADS,
    ),
    Ship(
        name="USS Phantom",
        boat_command_channel_id=BC_PHANTOM,
        role_id=ROLE_ID_PHANTOM,
        emoji="<:Phantom:1375148736472158228>",
        size=SIZE_2_SQUADS,
    ),
    Ship(
        name="USS Silverclaw",
        boat_command_channel_id=BC_SILVERCLAW,
        role_id=ROLE_ID_SILVERCLAW,
        emoji="<:Silverclaw_emoji:1345475394169475104>",
        size=SIZE_3_SQUADS,
    ),
    Ship(
        name="USS Venom",
        boat_command_channel_id=BC_VENOM,
        role_id=ROLE_ID_VENOM,
        emoji="<:Venom:1239895956489633852>",
        size=SIZE_2_SQUADS,
    ),
    Ship(
        name="USS Titan",
        boat_command_channel_id=BC_TITAN,
        role_id=ROLE_ID_TITAN,
        emoji="<:Titan:1352591957804978277>",
        size=SIZE_2_SQUADS,
    ),
]
