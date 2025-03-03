from src.config.main_server import (
    BC_ADRESTIA,
    BC_ADUN,
    BC_ARIZONA,
    BC_COLLINS,
    BC_HYPERION,
    BC_LUSTY,
    BC_MAELSTROM,
    BC_PHANTOM,
    BC_PLATYPUS,
    BC_SILVERCLAW,
    BC_VALHALLA,
    BC_VENOM,
)
from src.data.structs import Ship

ROLE_ID_LUSTY = 933919139700019222
ROLE_ID_VALHALLA = 1164671319338664007
ROLE_ID_MAELSTROM = 1002303636522680391
ROLE_ID_ADUN = 1242143582463332402
ROLE_ID_ADRESTIA = 1084451910578339880
ROLE_ID_HYPERION = 1157426517912076318
ROLE_ID_PLATYPUS = 967531117882261536
ROLE_ID_ARIZONA = 1058840733248933908
ROLE_ID_PHANTOM = 1274251672876617792
ROLE_ID_SILVERCLAW = 977935623774162954
ROLE_ID_VENOM = 1237838106711822457
ROLE_ID_COLLINS = 1247405133130764329

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
        name="USS Reliant",
        boat_command_channel_id=BC_MAELSTROM,
        role_id=ROLE_ID_MAELSTROM,
        emoji="<:Maelstrom:1259650992346107944>",
    ),
    Ship(
        name="USS Adun",
        boat_command_channel_id=BC_ADUN,
        role_id=ROLE_ID_ADUN,
        emoji="<:Adun:1251266293601013871>",
    ),
    Ship(
        name="USS Adrestia",
        boat_command_channel_id=BC_ADRESTIA,
        role_id=ROLE_ID_ADRESTIA,
        emoji="<:adrestia:1201500831015506031>",
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
        name="USS Arizona",
        boat_command_channel_id=BC_ARIZONA,
        role_id=ROLE_ID_ARIZONA,
        emoji="<:Arizona:1238520496442839150>",
    ),
    Ship(
        name="USS Phantom",
        boat_command_channel_id=BC_PHANTOM,
        role_id=ROLE_ID_PHANTOM,
        emoji="<:Phantom:1274254756730109953>",
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
        name="USS Journey",
        boat_command_channel_id=BC_COLLINS,
        role_id=ROLE_ID_COLLINS,
        emoji="<:Collins:1263703567978729593>",
    ),
]
