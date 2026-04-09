from __future__ import annotations

from collections.abc import Mapping

from src.utils.discord_utils import EngineerAlertField
from src.utils.emoji_utils import render_ship_label


def build_ship_overview_field(
        per_ship_counts: Mapping[int | None, int],
        *,
        label: str = "Ship Overview",
) -> EngineerAlertField | None:
    normalized_counts = {
        ship_role_id: count
        for ship_role_id, count in per_ship_counts.items()
        if count > 0
    }
    if not normalized_counts:
        return None

    lines = [
        f"{render_ship_label(ship_role_id=ship_role_id)}: **{count}**"
        for ship_role_id, count in sorted(
            normalized_counts.items(),
            key=lambda item: (-item[1], item[0] or 0),
        )
    ]
    return EngineerAlertField(label, "\n".join(lines))
