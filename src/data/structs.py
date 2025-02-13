from __future__ import annotations

from logging import getLogger
from collections import OrderedDict
from dataclasses import dataclass
from warnings import warn

import config.ranks_roles
from config.main_server import GUILD_ID
from discord import Guild, Member, Role


log = getLogger(__name__)

@dataclass
class Ship:
    name: str = None # Ship name e.g. "USS Venom"
    role_id: int = None # Role ID of the ship
    boat_command_channel_id: int = None # Channel ID of the ship's boat command channel (e.g. BC_VENOM)
    emoji: str = None # Emoji of the ship

@dataclass
class Abbreviation:
    abbreviation: str = None # The abbreviation
    meaning: str = None # The meaning of the abbreviation

@dataclass
class RankAbbreviation(Abbreviation):
    associated_rank: NavyRank = None # The rank that the abbreviation is associated with

@dataclass
class Context:
    short_description: str = None # Short definition of the abbreviation

    channel_id: int = None # Could be either a channel or channel_thread id
    message_id: int = None # ID of the message/embed within the channel

    @property
    def embed_url(self) -> str:
        if self.message_id == 0 or self.channel_id == 0:
            return None
        return f"https://discord.com/channels/{GUILD_ID}/{self.channel_id}/{self.message_id}"

@dataclass
class RankPrerequisites:
    additional_requirements: list[str] = list

@dataclass
class NavyRank:
    index: int = 0 # The index of the rank in the hierarchy (0 is the highest rank)
    identifier: str = "" # The identifier of the rank (e.g. "E1", "O1", "DH")
    role_ids: tuple[int] = () # The role IDs associated with the rank (e.g. [933913081099214848] for Recruit)
    name: str = "" # The name of the rank (e.g. "Recruit", "Midshipman")
    marine_name: str = name # The name of the rank in case they are a Marine
    promotion_index: set[int] = () # The index of the rank that the member would be promoted to
    rank_prerequisites: RankPrerequisites = None # The requirements needed for a rank
    rank_context: Context = None # The context of the rank (e.g. the channel_thread_id and message_id of the rank's embed)

@dataclass
class Award:
    threshold: int = 0
    ranks_responsible: str = ""
    role_id: int = 0
    embed_id: int = 0
    channelthread_id: int = 0

    @property
    def embed_url(self) -> str:
        return f"https://discord.com/channels/{GUILD_ID}/{self.channelthread_id}/{self.embed_id}"


@dataclass
class CombatAward(Award):
    streak: bool = True

@dataclass
class AwardsCollector:
    voyages: tuple[Award]
    hosted: tuple[Award]
    combat: tuple[CombatAward]
    training: tuple[Award]
    recruit: tuple[Award]
    attendance: tuple[Award]
    service: tuple[Award]

@dataclass
class SubclassCollector:
    cannoneer: tuple[Award]
    carpenter: tuple[Award]
    flex: tuple[Award]
    grenadier: tuple[Award]
    helm: tuple[Award]
    surgeon: tuple[Award]

@dataclass
class SailorCO:
    immediate: Member | None
    acting: Member | None
    _sailor: Member
    _guild: Guild

    def __init__(self, sailor: Member, guild: Guild):
        self.immediate = None
        self.acting = None
        self._sailor = sailor
        self._guild = guild

        # Unpack sailor roles
        sailor_roles = sailor.roles
        role_ids = set([role.id for role in sailor_roles])

        # Traverse the chain of command
        co_set = False
        CoC = config.ranks_roles.CHAIN_OF_COMMAND
        CoC_keys = list(CoC.keys())
        for role_id in CoC_keys:
            if role_id in role_ids:
                co_member = _get_co_from_link(role_id, sailor, CoC, CoC_keys, guild)
                self.immediate = co_member
                co_set = True
                break

        # Get Squad Leader
        if not co_set:
            role_found = False
            for role in sailor_roles:
                if role.name.upper().endswith(' SQUAD'):
                    squad_role = role
                    role_found = True
                    break
            if role_found:
                for role_member in squad_role.members:
                    if config.ranks_roles.SHIP_SL_ROLE in (role.id for role in role_member.roles):
                        squad_leader = role_member
                        self.immediate = squad_leader
                        break

        # Get the acting CO (if immediate CO is LOA-2)
        self.acting = self.immediate
        if self.immediate and self.immediate.display_name.startswith("[LOA-2]"):
            self.acting = SailorCO(self.immediate, guild).acting

    def for_awards(self, award_roles: tuple[int]) -> Member | Role:
        # Check if top of CoC
        CoC = config.ranks_roles.CHAIN_OF_COMMAND
        CoC_keys = list(CoC.keys())
        if CoC_keys[0] in [role.id for role in self._sailor.roles]:
            boa_role = self._guild.get_role(config.ranks_roles.BOA_ROLE)
            return boa_role

        # Check if acting CO has roles
        acting_role_ids = set([role.id for role in self.acting.roles])
        for award_role in award_roles:
            if award_role in acting_role_ids:
                return self.acting

        # Re-run for the acting CO's acting CO if not
        return SailorCO(self.acting, self._guild).for_awards(award_roles)

    @property
    def member_str(self) -> str:
        if self.acting is None:
            return "None"
        if self.acting.id == self.immediate.id:
            return f"<@{self.acting.id}>"
        return f"Current: <@{self.acting.id}>\nImmediate: <@{self.immediate.id}>"

def _get_co_from_link(role_id: int, sailor: Member, CoC: OrderedDict, CoC_keys: list[int], guild: Guild) -> Member | None:
    co_role_id, common_group = CoC[role_id]
    if co_role_id is None:
        return None

    co_role = guild.get_role(co_role_id)
    if common_group == config.ranks_roles.COC_ENUM['Fleet']:
        fleet_role = _get_fleet(sailor)
        co_role_members = [m for m in co_role.members if fleet_role in m.roles]
    elif common_group == config.ranks_roles.COC_ENUM['Ship']:
        ship_role = _get_ship(sailor)
        co_role_members = [m for m in co_role.members if ship_role in m.roles]
    else:
        co_role_members = co_role.members

    if len(co_role_members) == 1:
        return co_role_members[0]
    if len(co_role_members) == 0:
        # go up one in the CoC
        return _get_co_from_link(co_role_id, sailor, CoC, CoC_keys, guild)

    warn("Found more than one member with role. Using first in list")
    return co_role_members[0]

def _get_by_role(role_key: Role, members: list[Member]):
    member_with_role = None
    for member in members:
        if role_key in member.roles:
            member_with_role = member
            break
    return member_with_role

def _get_fleet(sailor: Member):
    fleet_role = None
    for role in sailor.roles:
        if role.name.endswith('Fleet'):
            fleet_role = role
            break
    return fleet_role

def _get_ship(sailor: Member):
    ship_role = None
    for role in sailor.roles:
        if role.name.startswith('USS'):
            ship_role = role
            break
    return ship_role
