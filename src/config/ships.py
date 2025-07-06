from src.config.main_server import (
    BC_GLETSJER,
    BC_ADUN,
    BC_DEFIANT,
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
from src.data.structs import Ship, Fleet, NavyFleetCollector

SHIP_MAX_SIZE = 30

ROLE_ID_ANCIENT_ISLES = 1023268709009207328
ROLE_ID_LUSTY = 933919139700019222
ROLE_ID_BERSERKER = 1164671319338664007
ROLE_ID_SERENITY = 1002303636522680391

ROLE_ID_DEVILS_ROAR = 1074458114637713509
ROLE_ID_DEFIANT = 1058840733248933908
ROLE_ID_SILVERCLAW = 977935623774162954
ROLE_ID_VENOM = 1237838106711822457

ROLE_ID_SHORES_OF_PLENTY = 1161861443004678315
ROLE_ID_TITAN = 1247405133130764329
ROLE_ID_GLETSJER = 1084451910578339880
ROLE_ID_PHANTOM = 1274251672876617792

ROLE_ID_WILDS = 933919084616228874
ROLE_ID_ADUN = 1242143582463332402
ROLE_ID_HYPERION = 1157426517912076318
ROLE_ID_NIGHTINGALE = 967531117882261536

###############################################################################
# Ships - Ship objects
###############################################################################

# Ancient Isles Fleet
#######################################
USS_ILLUSTRIOUS = Ship(
    name="USS Illustrious",
    boat_command_channel_id=BC_LUSTY,
    role_id=ROLE_ID_LUSTY,
    emoji="<:Lusty:1079841997021524018>",
)

USS_BERSERKER = Ship(
    name="USS Berserker",
    boat_command_channel_id=BC_BERSERKER,
    role_id=ROLE_ID_BERSERKER,
    emoji="<:Berserker:1390427238922719275>",
)

USS_SERENITY = Ship(
    name="USS Serenity",
    boat_command_channel_id=BC_SERENITY,
    role_id=ROLE_ID_SERENITY,
    emoji="<:Serenity:1356016930032713879>",
)

ANCIENT_ISLES_FLEET = Fleet(
    name="Ancient Isles Fleet",
    ships=(USS_ILLUSTRIOUS, USS_BERSERKER, USS_SERENITY),
    role_id=ROLE_ID_ANCIENT_ISLES,
    flagship=None,
    emoji="<:AncientIsles:1270890719405408378>",
)

# Devil's Roar Fleet
#######################################
USS_DEFIANT = Ship(
    name="USS Defiant",
    boat_command_channel_id=BC_DEFIANT,
    role_id=ROLE_ID_DEFIANT,
    emoji="<:Defiant:1354503521747075072>",
)

USS_SILVERCLAW = Ship(
    name="USS Silverclaw",
    boat_command_channel_id=BC_SILVERCLAW,
    role_id=ROLE_ID_SILVERCLAW,
    emoji="<:Silverclaw_emoji:1345475394169475104>",
)

USS_VENOM = Ship(
    name="USS Venom",
    boat_command_channel_id=BC_VENOM,
    role_id=ROLE_ID_VENOM,
    emoji="<:Venom:1239895956489633852>",
)

DEVILS_ROAR_FLEET = Fleet(
    name="The Devil's Roar Fleet",
    ships=(USS_DEFIANT, USS_SILVERCLAW, USS_VENOM),
    role_id=ROLE_ID_DEVILS_ROAR,
    flagship="USS Defiant",
    emoji="<:DevilsRoar:1270890826574204988>",
)

# Shores of Plenty Fleet
#######################################
USS_TITAN = Ship(
    name="USS Titan",
    boat_command_channel_id=BC_TITAN,
    role_id=ROLE_ID_TITAN,
    emoji="<:Titan:1352591957804978277>",
)

USS_GLETSJER = Ship(
    name="USS Gletsjer",
    boat_command_channel_id=BC_GLETSJER,
    role_id=ROLE_ID_GLETSJER,
    emoji="<:Gletsjer:1356717285171265818>",
)

USS_PHANTOM = Ship(
    name="USS Phantom",
    boat_command_channel_id=BC_PHANTOM,
    role_id=ROLE_ID_PHANTOM,
    emoji="<:Phantom:1375148736472158228>",
)

SHORES_OF_PLENTY_FLEET = Fleet(
    name="Shores of Plenty Fleet",
    ships=(USS_TITAN, USS_GLETSJER, USS_PHANTOM),
    role_id=1161861443004678315,
    flagship=None,
    emoji="<:ShoresOfPlenty:1270890631979597864>",
)


# Wilds Fleet
#######################################
USS_ADUN = Ship(
    name="USS Adun",
    boat_command_channel_id=BC_ADUN,
    role_id=ROLE_ID_ADUN,
    emoji="<:Adun:1251266293601013871>",
)

USS_HYPERION = Ship(
        name="USS Hyperion",
        boat_command_channel_id=BC_HYPERION,
        role_id=ROLE_ID_HYPERION,
        emoji="<:hyperion1:1162043891185369199>",
    )

USS_NIGHTINGALE = Ship(
        name="USS Nightingale",
        boat_command_channel_id=BC_NIGHTINGALE,
        role_id=ROLE_ID_NIGHTINGALE,
        emoji="<:nightingale:1382145592934924370>",
    )

WILDS_FLEET = Fleet(
    name="The Wilds Fleet",
    ships=(USS_ADUN, USS_HYPERION, USS_NIGHTINGALE),
    role_id=933919084616228874,
    flagship=None,
    emoji="<:Wilds:1270890769292591134>",
)

# Navy collector
#######################################
FLEETS_OF_THE_NAVY = NavyFleetCollector(
    ancient_isles=ANCIENT_ISLES_FLEET,
    devils_roar=DEVILS_ROAR_FLEET,
    shores_of_plenty=SHORES_OF_PLENTY_FLEET,
    wilds=WILDS_FLEET,
)

SHIPS = FLEETS_OF_THE_NAVY.ships
