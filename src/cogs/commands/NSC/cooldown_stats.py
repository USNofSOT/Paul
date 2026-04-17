from __future__ import annotations

from logging import getLogger
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from src.security import require_any_role, Role, resolve_effective_roles
from src.utils.embeds import default_embed, error_embed

log = getLogger(__name__)


def _empty_cooldown_stats(command_name: str) -> dict[str, Any]:
    normalized_command_name = normalize_command_name(command_name)
    cooldown_config = get_command_cooldown_config(normalized_command_name)
    return {
        "command_name": normalized_command_name,
        "cooldown_seconds": cooldown_config.seconds,
        "trigger_count": 0,
        "last_triggered_at": None,
        "last_retry_after_seconds": 0,
    }


def is_nsc_user(member: discord.Member) -> bool:
    user_roles = resolve_effective_roles(member)
    return Role.NSC_OPERATOR in user_roles


def fetch_stored_cooldown_stats() -> dict[str, dict[str, Any]]:
    repository = CommandCooldownStatsRepository()
    try:
        stored_stats = {}
        for stat in repository.find():
            normalized_command_name = normalize_command_name(stat.command_name)
            stored_stats[normalized_command_name] = {
                "command_name": normalized_command_name,
                "cooldown_seconds": stat.cooldown_seconds,
                "trigger_count": stat.trigger_count,
                "last_triggered_at": stat.last_triggered_at,
                "last_retry_after_seconds": stat.last_retry_after_seconds,
            }
        return stored_stats
    finally:
        repository.close_session()


def build_cooldown_snapshots() -> dict[str, dict[str, Any]]:
    stored_stats = fetch_stored_cooldown_stats()
    command_names = sorted(set(COMMAND_COOLDOWNS) | set(stored_stats))

    snapshots = {}
    for command_name in command_names:
        snapshot = _empty_cooldown_stats(command_name)
        snapshot.update(stored_stats.get(command_name, {}))
        cooldown_config = get_command_cooldown_config(command_name)
        snapshot["cooldown_seconds"] = cooldown_config.seconds
        snapshots[command_name] = snapshot
    return snapshots


def _truncate_text(value: str | None, limit: int = 1000) -> str:
    if not value:
        return "None recorded."
    return sanitize_cooldown_text(
        value,
        limit=limit,
        escape_markdown=True,
    )


def _format_last_triggered(value) -> str:
    if value is None:
        return "Never"
    return f"<t:{int(value.timestamp())}:R>"


def _chunked(values: list[str], size: int) -> list[list[str]]:
    return [values[index:index + size] for index in range(0, len(values), size)]


def _top_snapshots(
        snapshots: list[dict[str, Any]],
        *,
        limit: int,
        key,
) -> list[dict[str, Any]]:
    return sorted(snapshots, key=key)[:limit]


def _build_snapshot_line(snapshot: dict[str, Any]) -> str:
    return (
        f"`{snapshot['command_name']}` | **{snapshot['cooldown_seconds']}s** | "
        f"hits **{snapshot['trigger_count']}** | "
        f"last {_format_last_triggered(snapshot['last_triggered_at'])}"
    )


def build_overview_embeds() -> list[discord.Embed]:
    snapshots = list(build_cooldown_snapshots().values())
    enabled_snapshots = [
        item for item in snapshots if item["cooldown_seconds"] > 0
    ]
    triggered_snapshots = [
        item for item in snapshots if item["trigger_count"] > 0
    ]

    total_commands = len(snapshots)
    enabled_commands = len(enabled_snapshots)
    total_triggers = sum(item["trigger_count"] for item in snapshots)
    commands_hit = len(triggered_snapshots)
    hottest_command = max(
        snapshots,
        key=lambda item: item["trigger_count"],
        default=None,
    )

    summary_embed = default_embed(
        title="Cooldown Overview",
        description="Configured cooldowns and tracked cooldown hits.",
    )
    summary_embed.add_field(
        name="Summary",
        value=(
            f"Commands tracked: **{total_commands}**\n"
            f"Cooldowns enabled: **{enabled_commands}**\n"
            f"Commands hit: **{commands_hit}**\n"
            f"Cooldown hits: **{total_triggers}**\n"
            f"Hottest command: **"
            f"{hottest_command['command_name'] if hottest_command else 'None'}**"
        ),
        inline=False,
    )

    longest_cooldowns = _top_snapshots(
        enabled_snapshots,
        limit=10,
        key=lambda item: (-item["cooldown_seconds"], item["command_name"]),
    )
    most_triggered = _top_snapshots(
        triggered_snapshots,
        limit=10,
        key=lambda item: (-item["trigger_count"], item["command_name"]),
    )
    recently_triggered = _top_snapshots(
        triggered_snapshots,
        limit=10,
        key=lambda item: (
            -(item["last_triggered_at"].timestamp())
            if item["last_triggered_at"] is not None
            else float("inf"),
            item["command_name"],
        ),
    )

    summary_embed.add_field(
        name="Longest Cooldowns",
        value=(
            "\n".join(_build_snapshot_line(item) for item in longest_cooldowns)
            if longest_cooldowns
            else "No cooldowns configured."
        ),
        inline=False,
    )
    summary_embed.add_field(
        name="Most Triggered",
        value=(
            "\n".join(_build_snapshot_line(item) for item in most_triggered)
            if most_triggered
            else "No cooldown hits recorded."
        ),
        inline=False,
    )
    summary_embed.add_field(
        name="Recently Triggered",
        value=(
            "\n".join(_build_snapshot_line(item) for item in recently_triggered)
            if recently_triggered
            else "No recent cooldown hits."
        ),
        inline=False,
    )

    all_enabled_lines = [
        _build_snapshot_line(item)
        for item in sorted(
            enabled_snapshots,
            key=lambda item: (-item["cooldown_seconds"], item["command_name"]),
        )
    ]
    detail_embeds = []
    for page_number, page_lines in enumerate(_chunked(all_enabled_lines, 12), start=1):
        detail_embeds.append(
            default_embed(
                title=f"Enabled Cooldowns ({page_number})",
                description="\n".join(page_lines),
            )
        )

    return [summary_embed, *detail_embeds]


def build_single_command_embeds(command_name: str) -> list[discord.Embed]:
    normalized_command_name = normalize_command_name(command_name)
    snapshot = build_cooldown_snapshots()[normalized_command_name]

    overview_embed = default_embed(
        title=f"Cooldown Report: {normalized_command_name}",
        description="Tracking and configured cooldown details for this command.",
    )
    overview_embed.add_field(
        name="Configuration",
        value=(
            f"Cooldown: **{snapshot['cooldown_seconds']}s**"
        ),
        inline=False,
    )
    overview_embed.add_field(
        name="Activity",
        value=(
            f"Cooldown hits: **{snapshot['trigger_count']}**\n"
            f"Last retry after: **{snapshot['last_retry_after_seconds']}s**\n"
            f"Last triggered: **{_format_last_triggered(snapshot['last_triggered_at'])}**"
        ),
        inline=False,
    )
    return [overview_embed]


def build_cooldown_report_embeds(scope: str | None) -> list[discord.Embed]:
    if scope is None:
        return build_overview_embeds()

    scope_key = normalize_command_name(scope)
    snapshots = build_cooldown_snapshots()
    if scope_key not in snapshots:
        raise KeyError(scope)
    return build_single_command_embeds(scope_key)


class ConfirmClearCooldownStatsView(discord.ui.View):
    def __init__(self, report_view: "CooldownStatsReportView"):
        super().__init__(timeout=120)
        self.report_view = report_view

    @discord.ui.button(label="Confirm Clear", style=discord.ButtonStyle.danger)
    async def confirm_clear(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button,
    ):
        del button
        if not is_nsc_user(interaction.user):
            await interaction.response.send_message(
                embed=error_embed(
                    title="Missing Permissions",
                    description="You do not have permission to clear cooldown stats.",
                ),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        repository = CommandCooldownStatsRepository()
        try:
            deleted_rows = repository.clear_all_command_cooldown_stats()
        finally:
            repository.close_session()

        await self.report_view.refresh_message()
        await interaction.response.edit_message(
            content=f"Cleared **{deleted_rows}** cooldown stat rows.",
            embed=None,
            view=None,
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_clear(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button,
    ):
        del button
        await interaction.response.edit_message(
            content="Cancelled clearing cooldown stats.",
            embed=None,
            view=None,
        )


class CooldownStatsControls(discord.ui.Select):
    def __init__(self, report_view: "CooldownStatsReportView"):
        self.report_view = report_view
        options = [
            discord.SelectOption(
                label="Refresh Report",
                value="refresh",
                description="Rebuild the current cooldown report.",
            ),
            discord.SelectOption(
                label="Clear Cooldown Stats Rows",
                value="clear_stats",
                description="Delete all rows from the cooldown stats table.",
            ),
        ]
        super().__init__(
            placeholder="NSC controls",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        if not is_nsc_user(interaction.user):
            await interaction.response.send_message(
                embed=error_embed(
                    title="Missing Permissions",
                    description="You do not have permission to use these controls.",
                ),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        selected = self.values[0]
        if selected == "refresh":
            await self.report_view.refresh_message()
            await interaction.response.send_message(
                "Cooldown report refreshed.",
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        if selected == "clear_stats":
            await interaction.response.send_message(
                "This will delete all rows from `command_cooldown_stats`. Confirm?",
                view=ConfirmClearCooldownStatsView(self.report_view),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )


class CooldownStatsReportView(discord.ui.View):
    def __init__(self, scope: str | None):
        super().__init__(timeout=300)
        self.scope = scope
        self.message: discord.Message | None = None
        self.add_item(CooldownStatsControls(self))

    async def refresh_message(self) -> None:
        if self.message is None:
            return
        await self.message.edit(
            embeds=build_cooldown_report_embeds(self.scope),
            view=self,
        )


class CooldownStats(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="cooldownstats",
        description="View configured cooldowns and tracked cooldown hits.",
    )
    @require_any_role(Role.NSC_OBSERVER)
    @app_commands.describe(
        scope="Optional command name to inspect.",
        hidden="Should only you be able to see the response?",
    )
    async def cooldown_stats(
            self,
            interaction: discord.Interaction,
            scope: str | None = None,
            hidden: bool = True,
    ):
        await interaction.response.defer(ephemeral=hidden)

        try:
            embeds = build_cooldown_report_embeds(scope)
        except KeyError:
            await interaction.followup.send(
                embed=error_embed(
                    title="Unknown command",
                    description=f"Unknown command: `{_truncate_text(scope, 100)}`",
                ),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return
        except Exception as e:
            log.error("Error retrieving cooldown stats: %s", e, exc_info=True)
            await interaction.followup.send(
                embed=error_embed(
                    title="Cooldown stats unavailable",
                    description="Unable to build the cooldown report right now.",
                    footer=False,
                ),
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        view = CooldownStatsReportView(scope)
        message = await interaction.followup.send(
            embeds=embeds,
            view=view,
            ephemeral=hidden,
            wait=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        view.message = message

    async def _autocomplete_scope(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> list[app_commands.Choice[str]]:
        del interaction
        options = sorted(build_cooldown_snapshots())
        current_lower = normalize_command_name(current)
        matching_options = [
            option for option in options if current_lower in option.lower()
        ]
        return [
            app_commands.Choice(name=option, value=option)
            for option in matching_options[:25]
        ]

    @cooldown_stats.autocomplete("scope")
    async def cooldown_stats_scope_autocomplete(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> list[app_commands.Choice[str]]:
        return await self._autocomplete_scope(interaction, current)


async def setup(bot: commands.Bot):
    await bot.add_cog(CooldownStats(bot))
