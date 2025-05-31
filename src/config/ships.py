from src.config.main_server import (
    BC_GLETSJER,
    BC_ADUN,
    BC_ARIZONA,
    BC_HYPERION,
    BC_LUSTY,
    BC_SERENITY,
    BC_PHANTOM,
    BC_PLATYPUS,
    BC_SILVERCLAW,
    BC_TITAN,
    BC_VALHALLA,
    BC_VENOM,
)
from src.data.structs import Ship

ROLE_ID_LUSTY = 933919139700019222
ROLE_ID_VALHALLA = 1164671319338664007
ROLE_ID_SERENITY = 1002303636522680391
ROLE_ID_ADUN = 1242143582463332402
ROLE_ID_GLETSJER = 1084451910578339880
ROLE_ID_HYPERION = 1157426517912076318
ROLE_ID_PLATYPUS = 967531117882261536
ROLE_ID_ARIZONA = 1058840733248933908
ROLE_ID_PHANTOM = 1274251672876617792
ROLE_ID_SILVERCLAW = 977935623774162954
ROLE_ID_VENOM = 1237838106711822457
ROLE_ID_TITAN = 1247405133130764329

###############################################################################
# Ships - Ship objects
###############################################################################
SHIPS = [
    Ship(
        name="USS Illustrious",
        boat_command_channel_id=BC_LUSTY,
        role_id=ROLE_ID_LUSTY,
        emoji="<:Lusty:1079841997021524018>",
    ),
    Ship(
        name="USS Valhalla",
        boat_command_channel_id=BC_VALHALLA,
        role_id=ROLE_ID_VALHALLA,
        emoji="<:valhalla:1345380823947542590>",
    ),
    Ship(
        name="USS Serenity",
        boat_command_channel_id=BC_SERENITY,
        role_id=ROLE_ID_SERENITY,
        emoji="<:Serenity:1356016930032713879>",
    ),
    Ship(
        name="USS Adun",
        boat_command_channel_id=BC_ADUN,
        role_id=ROLE_ID_ADUN,
        emoji="<:Adun:1251266293601013871>",
    ),
    Ship(
        name="USS Gletsjer",
        boat_command_channel_id=BC_GLETSJER,
        role_id=ROLE_ID_GLETSJER,
        emoji="<:Gletsjer:1356717285171265818>",
    ),
    Ship(
        name="USS Hyperion",
        boat_command_channel_id=BC_HYPERION,
        role_id=ROLE_ID_HYPERION,
        emoji="<:hyperion1:1162043891185369199>",
    ),
    Ship(
        name="USS Platypus",
        boat_command_channel_id=BC_PLATYPUS,
        role_id=ROLE_ID_PLATYPUS,
        emoji="<:Platypus:1282806780342177845>",
    ),
    Ship(
        name="USS Defiant",
        boat_command_channel_id=BC_ARIZONA,
        role_id=ROLE_ID_ARIZONA,
        emoji="<:Defiant:1354503521747075072>",
    ),
    Ship(
        name="USS Phantom",
        boat_command_channel_id=BC_PHANTOM,
        role_id=ROLE_ID_PHANTOM,
        emoji="<:Phantom:1375148736472158228>",
    ),
    Ship(
        name="USS Silverclaw",
        boat_command_channel_id=BC_SILVERCLAW,
        role_id=ROLE_ID_SILVERCLAW,
        emoji="<:Silverclaw_emoji:1345475394169475104>",
    ),
    Ship(
        name="USS Venom",
        boat_command_channel_id=BC_VENOM,
        role_id=ROLE_ID_VENOM,
        emoji="<:Venom:1239895956489633852>",
    ),
    Ship(
        name="USS Titan",
        boat_command_channel_id=BC_TITAN,
        role_id=ROLE_ID_TITAN,
        emoji="<:Titan:1352591957804978277>",
    ),
]
