from dataclasses import dataclass, field
from functools import lru_cache
from logging import getLogger
from typing import Type

from data import Hosted, VoyageType
from data.repository.hosted_repository import HostedRepository

log = getLogger(__name__)


@dataclass
class ShipHostHistory:
    target_id: int  # The ID of the user that hosted the ship
    total_voyages: int  # The total number of voyages the user has made


@dataclass
class ShipVoyageTypeHistory:
    voyage_type: VoyageType
    total_voyages: int


@dataclass
class ShipHistory:
    history: list[Type[Hosted]]  # A list of Hosted objects, each representing a hosted ship entry
    ship_name: str  # The name of the ship
    is_auxiliary: bool  # Whether the ship is an auxiliary or not
    auxiliary_to: str | None  # The ship that the auxiliary is attached to (if applicable)
    total_voyages: int  # The total number of voyages the ship has made
    voyage_count: int  # The latest voyage count of the ship
    total_fishes_caught: int  # The total number of fishes caught by the ship
    total_gold_earned: int  # The total amount of gold earned by the ship
    total_doubloons_earned: int  # The total amount of doubloons earned by the ship
    total_ancient_coins_earned: int  # The total amount of ancient coins earned by the ship

    hosts: list[ShipHostHistory]  # A list of ShipHostHistory objects,
    # each representing a user that has hosted the ship
    voyage_types: list[ShipVoyageTypeHistory]  # A list of ShipVoyageTypeHistory objects,
    # each representing a voyage type that the ship has made

    def get_amount_of_voyage_type(self, voyage_type: VoyageType) -> int:
        return sum(1 for entry in self.history if entry.voyage_type == voyage_type)

    def get_top_three_hosts(
        self,
        within_id_list: list[int] | None = None,
    ) -> list[ShipHostHistory]:
        if within_id_list:
            return sorted(
                [entry for entry in self.hosts if entry.target_id in within_id_list],
                key=lambda x: x.total_voyages,
                reverse=True,
            )[:3]
        return sorted(self.hosts, key=lambda x: x.total_voyages, reverse=True)[:3]

    def get_top_three_voyage_types(
        self,
        ignore_unknown: bool = True,
    ) -> list[ShipVoyageTypeHistory]:
        if ignore_unknown:
            return sorted(
                [entry for entry in self.voyage_types if entry.voyage_type != VoyageType.UNKNOWN],
                key=lambda x: x.total_voyages,
                reverse=True,
            )[:3]
        return sorted(self.voyage_types, key=lambda x: x.total_voyages, reverse=True)[:3]

    def __init__(self, ship_name: str):
        hosted_repository = HostedRepository()
        ship_history = hosted_repository.retrieve_ship_history(ship_name)

        if not ship_history:
            raise ValueError(f"Ship '{ship_name}' does not have any history.")

        ship_history_sample: Type[Hosted] = ship_history[0]

        self.history = ship_history

        self.ship_name = ship_name
        self.is_auxiliary = ship_history_sample.auxiliary_ship_name is not None
        self.auxiliary_to = ship_history_sample.ship_name if self.is_auxiliary else None
        self.total_voyages = len(ship_history)
        self.voyage_count = max(entry.ship_voyage_count for entry in ship_history)
        self.total_fishes_caught = sum([entry.fish_count for entry in ship_history])
        self.total_gold_earned = sum([entry.gold_count for entry in ship_history])
        self.total_doubloons_earned = sum([entry.doubloon_count for entry in ship_history])
        self.total_ancient_coins_earned = sum([entry.ancient_coin_count for entry in ship_history])

        self.hosts = []
        for host in ship_history:
            if host.target_id not in [entry.target_id for entry in self.hosts]:
                self.hosts.append(
                    ShipHostHistory(
                        target_id=int(host.target_id),
                        total_voyages=len(
                            [entry for entry in ship_history if entry.target_id == host.target_id]
                        ),
                    )
                )
        self.voyage_types = []
        for voyage_type in VoyageType:
            self.voyage_types.append(
                ShipVoyageTypeHistory(
                    voyage_type=voyage_type,
                    total_voyages=len(
                        [
                            entry
                            for entry in ship_history
                            if entry.voyage_type.name == voyage_type.name
                        ]
                    ),
                )
            )
        hosted_repository.close_session()


@dataclass
class ShipName:
    main_ship_name: str
    auxiliary_ship_names: list[str] = field(default_factory=list)


@lru_cache(maxsize=32)
def _get_unique_ship_names() -> list[ShipName]:
    result = []
    hosted_repository = HostedRepository()
    try:
        # Retrieve unique ship names (main and auxiliary) from the database
        # index 0 is main ship name, 1 is auxiliary ship name
        ship_names = hosted_repository.retrieve_unique_ship_name_combinations()
        for main_ship, auxiliary_ship in ship_names:
            ship_name = next((s for s in result if s.main_ship_name == main_ship), None)
            if ship_name:
                if auxiliary_ship:
                    ship_name.auxiliary_ship_names.append(auxiliary_ship)
            else:
                result.append(
                    ShipName(
                        main_ship_name=main_ship,
                        auxiliary_ship_names=[auxiliary_ship] if auxiliary_ship else [],
                    )
                )
    except Exception as e:
        log.error("Error retrieving unique ship names.")
        raise e
    finally:
        hosted_repository.close_session()
    return result


def get_ship_names(
    get_main_ship_names: bool = True,
    get_auxiliary_ship_names: bool = True,
    map_by_main_ship_name: bool = False,
    ignore_none: bool = True,
) -> list[str] | dict[str, list[str]]:
    ship_names = _get_unique_ship_names()
    if ignore_none:
        ship_names = [ship for ship in ship_names if ship.main_ship_name is not None]
    if map_by_main_ship_name:
        return {ship.main_ship_name: ship.auxiliary_ship_names for ship in ship_names}
    if get_main_ship_names and get_auxiliary_ship_names:
        return sorted(
            [ship.main_ship_name for ship in ship_names]
            + [aux_ship for ship in ship_names for aux_ship in ship.auxiliary_ship_names]
        )
    if get_main_ship_names:
        return sorted([ship.main_ship_name for ship in ship_names])
    if get_auxiliary_ship_names:
        return sorted([aux_ship for ship in ship_names for aux_ship in ship.auxiliary_ship_names])
