from __future__ import annotations

from dataclasses import dataclass

DEFAULT_COMMAND_COOLDOWN_MESSAGE = (
    "Please wait {retry_after} seconds before using `{command_name}` again."
)


@dataclass(frozen=True)
class CommandCooldownConfig:
    seconds: int = 0
    message: str = DEFAULT_COMMAND_COOLDOWN_MESSAGE


def command_cooldown(
        seconds: int,
        message: str | None = None,
) -> CommandCooldownConfig:
    if seconds < 0:
        raise ValueError("Command cooldown seconds must be 0 or greater.")

    return CommandCooldownConfig(
        seconds=seconds,
        message=message or DEFAULT_COMMAND_COOLDOWN_MESSAGE,
    )


COMMAND_COOLDOWNS = {
    "abbreviations": command_cooldown(3),
    "addanycoin": command_cooldown(3),
    "addcoin": command_cooldown(3),
    "addinfo": command_cooldown(5),
    "addnote": command_cooldown(5),
    "addsubclass": command_cooldown(15),
    "botstatus": command_cooldown(5),
    "cachestats": command_cooldown(10),
    "check_awards": command_cooldown(10),
    "checkpromotion": command_cooldown(5),
    "coins_given": command_cooldown(5),
    "coins_received": command_cooldown(5),
    "commandsync": command_cooldown(120),
    "cooldownstats": command_cooldown(10),
    "crewreport": command_cooldown(20),
    "dumpnotes": command_cooldown(30),
    "forceadd": command_cooldown(10),
    "gamertags": command_cooldown(5),
    "grabtop": command_cooldown(10),
    "hidenote": command_cooldown(5),
    "jakserah": command_cooldown(3),
    "joke": command_cooldown(3),
    "logbook": command_cooldown(15),
    "logs": command_cooldown(10),
    "marinecommittee": command_cooldown(3),
    "marineprogress": command_cooldown(8),
    "member": command_cooldown(5),
    "netreport": command_cooldown(15),
    "ping": command_cooldown(3),
    "placerecruit": command_cooldown(5),
    "populate_training_records": command_cooldown(90),
    "populate_voyages": command_cooldown(120),
    "progress": command_cooldown(8),
    "removeanycoin": command_cooldown(3),
    "removecoin": command_cooldown(3),
    "ribbonboard": command_cooldown(15),
    "ship_history": command_cooldown(8),
    "ships": command_cooldown(20),
    "shownotes": command_cooldown(5),
    "trainingrecords": command_cooldown(8),
    "updatemembers": command_cooldown(30),
    "viewmoderation": command_cooldown(5),
    "voyage_drilldown": command_cooldown(12),
    "voyage_information": command_cooldown(10),
    "voyages": command_cooldown(8),
    "voyagetogether": command_cooldown(8),
    "voyagewith": command_cooldown(8),
}

DISABLED_COMMAND_COOLDOWN = command_cooldown(0)


def get_command_cooldown_config(command_name: str) -> CommandCooldownConfig:
    return COMMAND_COOLDOWNS.get(
        command_name.lower(),
        DISABLED_COMMAND_COOLDOWN,
    )
