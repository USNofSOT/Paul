from __future__ import annotations
from dataclasses import dataclass

from config.main_server import GUILD_ID

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
