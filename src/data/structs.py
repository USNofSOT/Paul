from __future__ import annotations

from logging import getLogger
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
import re
from warnings import warn

from config.discord import MAX_NICKNAME_LENGTH
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
    gender_options: dict = {}  # Gender-specific name options
    marine_gender_options: dict = {}
    abbreviations: tuple[str] = () # Official abbreviations of rank
    unofficial_abbreviations: tuple[str] = () # Unofficial abbreviations found in the server
    marine_abbreviations: tuple[str] = () # Official marine abbreviations
    unofficial_marine_abbreviations: tuple[str] = () # Unofficial abbreviations found in the server
    promotion_index: set[int] = () # The index of the rank that the member would be promoted to
    rank_prerequisites: RankPrerequisites = None # The requirements needed for a rank
    rank_context: Context = None # The context of the rank (e.g. the channel_thread_id and message_id of the rank's embed)

@dataclass
class RetirementEnum(Enum):
             #  Ret Level  , RANKS index 
    ACTIVE   = (0          , -1)
    VETERAN  = (1          ,  3)
    RETIRED  = (2          ,  2)

@dataclass
class RankedNickname:
    LOA: int = 0
    retirement_level: int = 0
    flag_officer: bool = False
    marine: bool = False
    rank: NavyRank
    gender_option: str = 'male'
    nick: str
    _rank_list: tuple[NavyRank]

    @classmethod
    def from_member(cls, member: Member, rank_list: tuple[NavyRank]):
        ranked_nick = cls()
        ranked_nick._rank_list = rank_list
        nickname_str = member.nick or member.name
        remaining_str = nickname_str
        member_role_ids = [role.id for role in member.roles]

        # LOA
        match = re.search(r"\[LOA-(\d+)\]", nickname_str)
        if match:
            level = int(match.group(1))
            ranked_nick.LOA = level
            remaining_str.lstrip(f"[LOA-{level}]").lstrip(" ")

        # Retirement Level
        for rt_level in RetirementEnum:
            if rt_level.name == "ACTIVE":
                continue
            level_id, idx = rt_level.value
            rank_data = rank_list[idx]

            at_level = any([role_id in member_role_ids for role_id in rank_data.role_ids])
            if at_level:
                # Set Level
                ranked_nick.retirement_level = level_id

                # Remove inidicator from name string
                indicator_found = False
                if rank_data.name in remaining_str:
                    remaining_str = remaining_str.lstrip(rank_data.name).lstrip(" ")
                    indicator_found = True
                abbrev_list = rank_data.abbreviations + rank_data.unofficial_abbreviations
                for abbrev in sorted(abbrev_list, key=len, reverse=True):
                    if not indicator_found and remaining_str.startswith(abbrev):
                        remaining_str = remaining_str.lstrip(abbrev).lstrip(" ")
                        indicator_found = True
                        break
                break

        # Flag Officer
        if remaining_str.startswith("Flag "):
            ranked_nick.flag_officer = True
            remaining_str.lstrip("Flag ", "")

        # Marine
        ranked_nick.marine = config.ranks_roles.MARINE_ROLE in member_role_ids

        # Rank
        found_rank = False
        ret_indices = [ret_level.value[1] for ret_level in RetirementEnum]
        for idx, rank in enumerate(rank_list):
            if idx in ret_indices:
                continue
            for rank_id in rank.role_ids:
                if rank_id in member_role_ids:
                    ranked_nick.rank = rank
                    found_rank = True
                    break
            if found_rank:
                break
        
        # Gender Option
        for option, rank_name in ranked_nick.rank.gender_options.items():
            if rank_name.upper() in remaining_str.upper():
                ranked_nick.gender_option = option
                break
        
        # Nick
        if ranked_nick.marine:
            official_abbrevs = ranked_nick.rank.marine_abbreviations
            unofficial_abbrevs = ranked_nick.rank.unofficial_marine_abbreviations
        else:
            official_abbrevs = ranked_nick.rank.abbreviations
            unofficial_abbrevs = ranked_nick.rank.unofficial_abbreviations
        abbrev_list = official_abbrevs + unofficial_abbrevs

        for abbrev in sorted(abbrev_list, key=len, reverse=True):
            if remaining_str.startswith(abbrev):
                remaining_str = remaining_str.lstrip(abbrev).lstrip(" ")
                break
        ranked_nick.nick = remaining_str.rstrip()
        return ranked_nick
    
    def __str__(self):
        # LOA tag
        if self.LOA:
            LOA_part = f"[LOA-{self.LOA}] "
        else:
            LOA_part = ""

        # Retirement indicator
        retd_options = ("")
        if self.retirement_level == RetirementEnum.VETERAN[0]:
            retd_rank = self._rank_list[RetirementEnum.VETERAN[1]]
            retd_options = retd_rank.abbreviations + retd_rank.name
        elif self.retirement_level == RetirementEnum.RETIRED[0]:
            retd_rank = self._rank_list[RetirementEnum.RETIRED[1]]
            retd_options = retd_rank.abbreviations + retd_rank.name
        
        # Rank Title
        if self.marine:
            if self.gender_option in self.rank.marine_gender_options:
                name = self.rank.marine_gender_options[self.gender_option]
            else:
                name = self.rank.marine_name
            abbrevs = self.rank.marine_abbreviations
        else:
            if self.gender_option in self.rank.gender_options:
                name = self.rank.gender_options[self.gender_option]
            else:
                name = self.rank.name
            abbrevs = self.rank.abbreviations
        rank_options = abbrevs + name

        # Nick
        nick = f" {self.nick}"

        # Find longest retired + rank combination
        remaining_characters = MAX_NICKNAME_LENGTH
        remaining_characters -= len(LOA_part)
        remaining_characters -= len(nick)

        longest_combo = ""
        for i, retd_str in enumerate(retd_options):
            for j, rank_str in enumerate(rank_options):
                if retd_str and self.flag_officer:
                    combo_str = f"{retd_str} Flag {rank_str}"
                elif retd_str:
                    combo_str = f"{retd_str} {rank_str}"
                elif self.flag_officer:
                    combo_str = f"Flag {rank_str}"
                else:
                    combo_str = rank_str
                if (len(combo_str) > len(longest_combo)) and (len(combo_str) <= remaining_characters):
                    longest_combo = combo_str
        
        full_nickname = f"{LOA_part}{longest_combo}{nick}"
        return full_nickname





        



        
        


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
