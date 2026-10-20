import asyncio
from datetime import datetime
from types import SimpleNamespace

import discord
from discord.ext import commands

import src.cogs.commands.BOA.analytics as analytics_module
from src.cogs import EXTENSIONS
from src.cogs.commands.BOA.analytics import (
    AnalyticsHub,
    AnalyticsReportView,
    CooldownFilterState,
    PingFilterState,
    RoleSizeFilterState,
    ShipFilterState,
    VoyageFilterState,
    _format_pair_counts_with_percent,
    _format_ship_counts_with_percent,
    _format_ship_pairing_counts_with_percent,
    _format_ship_pair_counts_with_percent,
    _format_user_counts_with_percent,
)


def test_analytics_hub_exposes_relevant_subcommands():
    assert issubclass(AnalyticsHub, commands.GroupCog)
    group_commands = AnalyticsHub.__cog_app_commands__

    assert AnalyticsHub.__cog_group_name__ == "analytics"
    assert {command.name for command in group_commands} >= {
        "voyages",
        "voyage-ranks",
        "companions",
        "ships",
        "ship-history",
        "pings",
        "rank-size",
        "cooldowns",
    }


def test_subcommand_parameters_are_section_specific():
    commands_by_name = {
        command.name: command for command in AnalyticsHub.__cog_app_commands__
    }

    rank_size_params = {
        param.name for param in commands_by_name["rank-size"].parameters
    }
    cooldown_params = {param.name for param in commands_by_name["cooldowns"].parameters}
    pings_params = {param.name for param in commands_by_name["pings"].parameters}

    assert "user" not in rank_size_params
    assert "ship" not in cooldown_params
    assert "voyage_type" not in pings_params


def _control_ids(view: discord.ui.View) -> set[str]:
    return {child.custom_id for child in view.children if child.custom_id}


def _control_types(view: discord.ui.View) -> dict[str, type[discord.ui.Item]]:
    return {
        child.custom_id: type(child)
        for child in view.children
        if child.custom_id
    }


def _range_values(view: discord.ui.View, custom_id: str) -> list[str]:
    for child in view.children:
        if child.custom_id == custom_id:
            return [option.value for option in child.options]
    raise AssertionError(f"Missing control: {custom_id}")


def test_voyage_view_has_relevant_interactive_controls():
    view = AnalyticsReportView(
        cog=AnalyticsHub(bot=None),
        owner_id=123,
        section="voyages",
        state=VoyageFilterState(range_label="30d", section="overview"),
        hidden=True,
    )

    assert _control_ids(view) == {
        "analytics:voyages:range",
        "analytics:voyages:ship",
        "analytics:voyages:user",
        "analytics:voyages:voyage_type",
        "analytics:voyages:refresh",
        "analytics:voyages:clear",
    }
    control_types = _control_types(view)
    assert issubclass(control_types["analytics:voyages:user"], discord.ui.UserSelect)
    assert issubclass(control_types["analytics:voyages:refresh"], discord.ui.Button)
    assert issubclass(control_types["analytics:voyages:clear"], discord.ui.Button)
    assert {"730d", "1825d", "all"} <= set(
        _range_values(view, "analytics:voyages:range")
    )


def test_ping_view_has_supported_controls_without_voyage_type():
    view = AnalyticsReportView(
        cog=AnalyticsHub(bot=None),
        owner_id=123,
        section="pings",
        state=PingFilterState(range_label="30d"),
        hidden=True,
    )

    assert _control_ids(view) == {
        "analytics:pings:range",
        "analytics:pings:ping_role",
        "analytics:pings:ship",
        "analytics:pings:user",
        "analytics:pings:vp_status",
    }
    assert "analytics:pings:voyage_type" not in _control_ids(view)
    assert issubclass(
        _control_types(view)["analytics:pings:user"],
        discord.ui.UserSelect,
    )


def test_rank_size_view_has_rank_controls_without_user_or_ship():
    view = AnalyticsReportView(
        cog=AnalyticsHub(bot=None),
        owner_id=123,
        section="rank-size",
        state=RoleSizeFilterState(range_label="90d"),
        hidden=True,
    )

    assert _control_ids(view) == {
        "analytics:rank-size:range",
        "analytics:rank-size:rank_group",
        "analytics:rank-size:rank",
        "analytics:rank-size:refresh",
        "analytics:rank-size:clear",
    }
    assert "analytics:rank-size:user" not in _control_ids(view)
    assert "analytics:rank-size:ship" not in _control_ids(view)
    assert {"730d", "1825d", "all"} <= set(
        _range_values(view, "analytics:rank-size:range")
    )


def test_cooldowns_view_does_not_expose_unsupported_filters():
    view = AnalyticsReportView(
        cog=AnalyticsHub(bot=None),
        owner_id=123,
        section="cooldowns",
        state=CooldownFilterState(scope="voyages"),
        hidden=True,
    )

    assert _control_ids(view) == {"analytics:cooldowns:refresh"}


def test_filter_state_all_values_clear_optional_service_filters():
    now = datetime(2026, 1, 1, 12, 0)
    voyage = VoyageFilterState(
        range_label="7d",
        section="overview",
        ship_role_id=111,
        user_id=222,
        voyage_type="skirmish",
    )

    voyage.apply_select("ship", "all")
    voyage.apply_select("user", "all")
    voyage.apply_select("voyage_type", "all")
    filters = voyage.to_service_filters(now)

    assert filters.ship_role_id is None
    assert filters.user_id is None
    assert filters.voyage_type is None


def test_ping_filter_state_maps_select_values_to_service_filters():
    now = datetime(2026, 1, 1, 12, 0)
    state = PingFilterState(
        range_label="1d",
        ping_role_id=111,
        ship_role_id=222,
        user_id=333,
        vp_status="vp",
    )

    filters = state.to_service_filters(now)

    assert filters.ping_role_id == 111
    assert filters.ship_role_id == 222
    assert filters.user_id == 333
    assert filters.has_vp_permission is True


def test_clear_filters_preserves_section_and_range():
    companion = VoyageFilterState(
        range_label="365d",
        section="companions",
        ship_role_id=111,
        user_id=222,
        voyage_type="convoy",
    )

    companion.clear_optional_filters()

    assert companion.range_label == "365d"
    assert companion.section == "companions"
    assert companion.ship_role_id is None
    assert companion.user_id == 222
    assert companion.voyage_type == "all"


def test_ship_filter_state_maps_fleet_and_voyage_type():
    now = datetime(2026, 1, 1, 12, 0)
    state = ShipFilterState(
        range_label="30d",
        ship_role_id=444,
        fleet="ancient_isles",
        voyage_type="patrol",
    )

    filters = state.to_activity_filters(now)

    assert filters.ship_role_id == 444
    assert filters.fleet_role_ids
    assert filters.voyage_type is not None


def test_percent_formatters_include_denominators_where_relevant():
    assert "50.0%" in _format_user_counts_with_percent([(123, 1)], 2)
    assert "25.0%" in _format_ship_counts_with_percent([(500, 1)], 4)
    assert "66.7%" in _format_pair_counts_with_percent([((1, 2), 2)], 3)
    assert "50.0%" in _format_ship_pair_counts_with_percent([((500, 600), 1)], 2)


def test_ship_pairing_formatter_keeps_single_ship_rows_and_hides_invalid_roles():
    result = _format_ship_pairing_counts_with_percent(
        [
            ((500,), 3),
            ((500, 600), 2),
            ((500, -1), 1),
        ],
        5,
    )

    assert "1. " in result
    assert " — **3** (60.0%)" in result
    assert " + " in result
    assert "<@&-1>" not in result
    assert "Unknown ship (-1)" in result


def test_long_and_all_time_ranges_are_registered_as_slash_choices():
    commands_by_name = {
        command.name: command for command in AnalyticsHub.__cog_app_commands__
    }

    voyages_range = next(
        param
        for param in commands_by_name["voyages"].parameters
        if param.name == "range"
    )
    rank_size_range = next(
        param
        for param in commands_by_name["rank-size"].parameters
        if param.name == "range"
    )

    assert {"730d", "1825d", "all"} <= {
        choice.value for choice in voyages_range.choices
    }
    assert {"730d", "1825d", "all"} <= {
        choice.value for choice in rank_size_range.choices
    }


def test_boa_legacy_analytics_cogs_are_not_loaded():
    assert not hasattr(analytics_module, "LegacyAnalytics")
    assert "src.cogs.commands.BOA.ping_usage" not in EXTENSIONS
    assert "src.cogs.commands.BOA.ranks" not in EXTENSIONS
    assert "src.cogs.commands.BOA.voyage_drilldown" not in EXTENSIONS


def test_analytics_cooldown_payload_builds_overview_embeds():
    view = AnalyticsReportView(
        cog=AnalyticsHub(bot=None),
        owner_id=123,
        section="cooldowns",
        state=CooldownFilterState(scope=None),
        hidden=True,
    )

    payload = asyncio.run(
        view.cog._build_report_payload(
            view,
            SimpleNamespace(guild=None),
        )
    )

    assert payload.embeds
    assert payload.embeds[0].title == "Cooldown Overview"


def test_analytics_cooldown_scope_autocomplete_returns_choices():
    choices = asyncio.run(
        AnalyticsHub(bot=None).cooldowns_scope_autocomplete(
            SimpleNamespace(),
            "ship",
        )
    )

    assert any(choice.value == "ships" for choice in choices)
