from __future__ import annotations

from logging import getLogger
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from src.security import require_any_role, Role, resolve_effective_roles
from src.utils.embeds import default_embed, error_embed

log = getLogger(__name__)


def format_cache_ttl(ttl_seconds: int) -> str:
    hours = ttl_seconds // 3600
    days, remaining_hours = divmod(hours, 24)

    if days and remaining_hours:
        return f"{days}d {remaining_hours}h"
    if days:
        return f"{days}d"
    return f"{hours}h"


def _empty_cache_stats() -> dict[str, int | float]:
    return {
        "request_count": 0,
        "cache_hit_count": 0,
        "cache_miss_count": 0,
        "cached_percent": 0.0,
        "janitor_run_count": 0,
        "janitor_removed_expired_count": 0,
        "janitor_removed_overflow_count": 0,
        "janitor_last_removed_expired": 0,
        "janitor_last_removed_overflow": 0,
        "janitor_last_remaining_items": 0,
    }


def is_nsc_user(member: discord.Member) -> bool:
    user_roles = resolve_effective_roles(member)
    return Role.NSC_OPERATOR in user_roles


def category_title(category: str) -> str:
    metadata = CACHE_CATEGORY_METADATA.get(
        category,
        {"label": category.title(), "emoji": "📦"},
    )
    return f"{metadata['emoji']} {metadata['label']}"


def fetch_stored_cache_stats() -> dict[str, dict[str, int | float]]:
    repository = CacheStatsRepository()
    try:
        stored_stats = {}
        for stat in repository.find():
            stored_stats[stat.cache_name] = {
                "request_count": stat.request_count,
                "cache_hit_count": stat.cache_hit_count,
                "cache_miss_count": stat.cache_miss_count,
                "cached_percent": stat.cached_percent,
                "janitor_run_count": stat.janitor_run_count,
                "janitor_removed_expired_count": (
                    stat.janitor_removed_expired_count
                ),
                "janitor_removed_overflow_count": (
                    stat.janitor_removed_overflow_count
                ),
                "janitor_last_removed_expired": (
                    stat.janitor_last_removed_expired
                ),
                "janitor_last_removed_overflow": (
                    stat.janitor_last_removed_overflow
                ),
                "janitor_last_remaining_items": (
                    stat.janitor_last_remaining_items
                ),
            }
        return stored_stats
    finally:
        repository.close_session()


def build_cache_snapshot(
        cache_config,
        stats: dict[str, int | float],
) -> dict[str, Any]:
    return {
        "name": cache_config.name,
        "category": cache_config.category,
        "directory": cache_config.directory,
        "extension": cache_config.extension,
        "version": cache_config.version,
        "ttl": format_cache_ttl(cache_config.ttl_seconds),
        "max_items": cache_config.max_items,
        "cached_items": get_cached_item_count(cache_config),
        **stats,
    }


def build_cache_snapshots() -> dict[str, dict[str, Any]]:
    stored_stats = fetch_stored_cache_stats()
    return {
        cache_name: build_cache_snapshot(
            cache_config,
            stored_stats.get(cache_name, _empty_cache_stats()),
        )
        for cache_name, cache_config in IMAGE_CACHES.items()
    }


def build_overview_embeds() -> list[discord.Embed]:
    snapshots = build_cache_snapshots()
    grouped_caches = group_image_caches_by_category()

    total_items = 0
    total_requests = 0
    total_hits = 0
    total_misses = 0
    total_janitor_runs = 0
    total_removed_expired = 0
    total_removed_overflow = 0

    summary_embed = default_embed(
        title="Cache Overview",
        description="A grouped report for all cache categories.",
    )

    detail_embeds: list[discord.Embed] = []
    for category, caches in grouped_caches.items():
        category_snapshots = [snapshots[name] for name in caches]
        metadata = CACHE_CATEGORY_METADATA.get(
            category,
            {"label": category.title(), "emoji": "📦"},
        )

        category_items = sum(item["cached_items"] for item in category_snapshots)
        category_capacity = sum(item["max_items"] for item in category_snapshots)
        category_requests = sum(item["request_count"] for item in category_snapshots)
        category_hits = sum(item["cache_hit_count"] for item in category_snapshots)
        category_misses = sum(item["cache_miss_count"] for item in category_snapshots)
        category_janitor_runs = sum(
            item["janitor_run_count"] for item in category_snapshots
        )
        category_hit_rate = (
            round((category_hits / category_requests) * 100, 2)
            if category_requests
            else 0
        )

        summary_embed.add_field(
            name=f"{metadata['emoji']} {metadata['label']}",
            value=(
                f"Items: **{category_items}/{category_capacity}**\n"
                f"Requests: **{category_requests}**\n"
                f"Hit rate: **{category_hit_rate:.2f}%**\n"
                f"Hits/Misses: **{category_hits}/{category_misses}**\n"
                f"Janitor runs: **{category_janitor_runs}**"
            ),
            inline=True,
        )

        category_embed = default_embed(
            title=f"{metadata['emoji']} {metadata['label']} Caches",
            description="Per-cache detail for this category.",
        )
        for item in category_snapshots:
            category_embed.add_field(
                name=item["name"],
                value=(
                    f"Items: **{item['cached_items']}/{item['max_items']}**\n"
                    f"TTL: **{item['ttl']}**\n"
                    f"Requests: **{item['request_count']}**\n"
                    f"Hit rate: **{item['cached_percent']:.2f}%**\n"
                    f"Janitor runs: **{item['janitor_run_count']}**"
                ),
                inline=True,
            )
        detail_embeds.append(category_embed)

        total_items += category_items
        total_requests += category_requests
        total_hits += category_hits
        total_misses += category_misses
        total_janitor_runs += category_janitor_runs
        total_removed_expired += sum(
            item["janitor_removed_expired_count"] for item in category_snapshots
        )
        total_removed_overflow += sum(
            item["janitor_removed_overflow_count"] for item in category_snapshots
        )

    overall_hit_rate = (
        round((total_hits / total_requests) * 100, 2)
        if total_requests
        else 0
    )
    summary_embed.add_field(
        name="Summary",
        value=(
            f"Cached items: **{total_items}**\n"
            f"Requests: **{total_requests}**\n"
            f"Hits/Misses: **{total_hits}/{total_misses}**\n"
            f"Overall hit rate: **{overall_hit_rate:.2f}%**\n"
            f"Janitor runs: **{total_janitor_runs}**\n"
            f"Removed expired/overflow: **"
            f"{total_removed_expired}/{total_removed_overflow}**"
        ),
        inline=False,
    )

    return [summary_embed, *detail_embeds]


def build_category_embeds(category: str) -> list[discord.Embed]:
    grouped_caches = group_image_caches_by_category()
    snapshots = build_cache_snapshots()
    category_snapshots = [snapshots[name] for name in grouped_caches[category]]

    summary_embed = default_embed(
        title=f"{category_title(category)} Cache Group",
        description="Grouped report for this cache category.",
    )
    for item in category_snapshots:
        summary_embed.add_field(
            name=item["name"],
            value=(
                f"Items: **{item['cached_items']}/{item['max_items']}**\n"
                f"TTL: **{item['ttl']}**\n"
                f"Requests: **{item['request_count']}**\n"
                f"Hit rate: **{item['cached_percent']:.2f}%**"
            ),
            inline=True,
        )

    janitor_embed = default_embed(
        title=f"{category_title(category)} Janitor History",
        description="Cleanup activity for this category.",
    )
    for item in category_snapshots:
        janitor_embed.add_field(
            name=item["name"],
            value=(
                f"Runs: **{item['janitor_run_count']}**\n"
                f"Removed total: **"
                f"{item['janitor_removed_expired_count']}/"
                f"{item['janitor_removed_overflow_count']}**\n"
                f"Last remaining: **{item['janitor_last_remaining_items']}**"
            ),
            inline=True,
        )

    return [summary_embed, janitor_embed]


def build_single_cache_embeds(cache_name: str) -> list[discord.Embed]:
    item = build_cache_snapshots()[cache_name]

    overview_embed = default_embed(
        title=f"Cache Report: {cache_name}",
        description=(
            f"{category_title(item['category'])}\n"
            f"Directory: `{item['directory']}`"
        ),
    )
    overview_embed.add_field(
        name="Traffic",
        value=(
            f"Requests: **{item['request_count']}**\n"
            f"Hit rate: **{item['cached_percent']:.2f}%**\n"
            f"Hits/Misses: **{item['cache_hit_count']}/"
            f"{item['cache_miss_count']}**"
        ),
        inline=True,
    )
    overview_embed.add_field(
        name="Retention",
        value=(
            f"Items: **{item['cached_items']}/{item['max_items']}**\n"
            f"TTL: **{item['ttl']}**\n"
            f"Extension: **{item['extension']}**"
        ),
        inline=True,
    )
    overview_embed.add_field(
        name="Version",
        value=f"Cache version: **{item['version']}**",
        inline=True,
    )

    janitor_embed = default_embed(
        title=f"Janitor Report: {cache_name}",
        description="Cleanup history for this cache.",
    )
    janitor_embed.add_field(
        name="Totals",
        value=(
            f"Runs: **{item['janitor_run_count']}**\n"
            f"Expired removed: **{item['janitor_removed_expired_count']}**\n"
            f"Overflow removed: **{item['janitor_removed_overflow_count']}**"
        ),
        inline=True,
    )
    janitor_embed.add_field(
        name="Last Run",
        value=(
            f"Expired removed: **{item['janitor_last_removed_expired']}**\n"
            f"Overflow removed: **{item['janitor_last_removed_overflow']}**\n"
            f"Remaining items: **{item['janitor_last_remaining_items']}**"
        ),
        inline=True,
    )
    return [overview_embed, janitor_embed]


def build_cache_report_embeds(scope: str | None) -> list[discord.Embed]:
    if scope is None:
        return build_overview_embeds()

    scope_key = scope.lower()
    if scope_key in IMAGE_CACHES:
        return build_single_cache_embeds(scope_key)

    grouped_caches = group_image_caches_by_category()
    if scope_key in grouped_caches:
        return build_category_embeds(scope_key)

    raise KeyError(scope)


class ConfirmClearCacheStatsView(discord.ui.View):
    def __init__(self, report_view: "CacheStatsReportView"):
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
                    description="You do not have permission to clear cache stats.",
                ),
                ephemeral=True,
            )
            return

        repository = CacheStatsRepository()
        try:
            deleted_rows = repository.clear_all_cache_stats()
        finally:
            repository.close_session()

        await self.report_view.refresh_message()
        await interaction.response.edit_message(
            content=f"Cleared **{deleted_rows}** cache stat rows.",
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
            content="Cancelled clearing cache stats.",
            embed=None,
            view=None,
        )


class ConfirmClearCacheItemsView(discord.ui.View):
    def __init__(self, report_view: "CacheStatsReportView"):
        super().__init__(timeout=120)
        self.report_view = report_view

    @discord.ui.button(
        label="Confirm Delete Cache Files",
        style=discord.ButtonStyle.danger,
    )
    async def confirm_clear_items(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button,
    ):
        del button
        if not is_nsc_user(interaction.user):
            await interaction.response.send_message(
                embed=error_embed(
                    title="Missing Permissions",
                    description="You do not have permission to clear cache files.",
                ),
                ephemeral=True,
            )
            return

        removed_items = 0
        for cache_config in IMAGE_CACHES.values():
            removed_items += clear_cached_items(cache_config)

        await self.report_view.refresh_message()
        await interaction.response.edit_message(
            content=f"Deleted **{removed_items}** cached files.",
            embed=None,
            view=None,
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_clear_items(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button,
    ):
        del button
        await interaction.response.edit_message(
            content="Cancelled deleting cache files.",
            embed=None,
            view=None,
        )


class CacheStatsControls(discord.ui.Select):
    def __init__(self, report_view: "CacheStatsReportView"):
        self.report_view = report_view
        options = [
            discord.SelectOption(
                label="Refresh Report",
                value="refresh",
                emoji="🔄",
                description="Rebuild the current cache report.",
            ),
            discord.SelectOption(
                label="Clear Cache Stats Rows",
                value="clear_stats",
                emoji="🗑️",
                description="Delete all rows from the cache stats table only.",
            ),
            discord.SelectOption(
                label="Delete All Cache Files",
                value="clear_items",
                emoji="🔥",
                description="Delete all cached files from disk across all caches.",
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
            )
            return

        selected = self.values[0]
        if selected == "refresh":
            await self.report_view.refresh_message()
            await interaction.response.send_message(
                "Cache report refreshed.",
                ephemeral=True,
            )
            return

        if selected == "clear_stats":
            await interaction.response.send_message(
                "This will delete all rows from `cache_stats` only. Confirm?",
                view=ConfirmClearCacheStatsView(self.report_view),
                ephemeral=True,
            )
            return

        if selected == "clear_items":
            await interaction.response.send_message(
                (
                    "This will delete all cached files from disk across every "
                    "configured cache. Confirm?"
                ),
                view=ConfirmClearCacheItemsView(self.report_view),
                ephemeral=True,
            )


class CacheStatsReportView(discord.ui.View):
    def __init__(self, scope: str | None):
        super().__init__(timeout=300)
        self.scope = scope
        self.message: discord.Message | None = None
        self.add_item(CacheStatsControls(self))

    async def refresh_message(self) -> None:
        if self.message is None:
            return
        await self.message.edit(
            embeds=build_cache_report_embeds(self.scope),
            view=self,
        )


class CacheStats(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="cachestats",
        description="View grouped cache stats, one category, or one cache.",
    )
    @require_any_role(Role.NSC_OBSERVER)
    @app_commands.describe(
        scope="Optional cache category or specific cache name.",
        hidden="Should only you be able to see the response?",
    )
    async def cache_stats(
            self,
            interaction: discord.Interaction,
            scope: str | None = None,
            hidden: bool = True,
    ):
        await interaction.response.defer(ephemeral=hidden)

        try:
            embeds = build_cache_report_embeds(scope)
        except KeyError:
            await interaction.followup.send(
                embed=error_embed(
                    title="Unknown cache",
                    description=f"Unknown cache or category: `{scope}`",
                ),
                ephemeral=True,
            )
            return
        except Exception as e:
            log.error("Error retrieving cache stats: %s", e, exc_info=True)
            await interaction.followup.send(embed=error_embed(exception=e))
            return

        view = CacheStatsReportView(scope)
        message = await interaction.followup.send(
            embeds=embeds,
            view=view,
            ephemeral=hidden,
            wait=True,
        )
        view.message = message

    async def _autocomplete_scope(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> list[app_commands.Choice[str]]:
        del interaction
        options = [
            *CACHE_CATEGORY_METADATA.keys(),
            *IMAGE_CACHES.keys(),
        ]
        current_lower = current.lower()
        matching_options = [
            option for option in options if current_lower in option.lower()
        ]
        return [
            app_commands.Choice(name=option, value=option)
            for option in matching_options[:25]
        ]

    @cache_stats.autocomplete("scope")
    async def cache_stats_scope_autocomplete(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> list[app_commands.Choice[str]]:
        return await self._autocomplete_scope(interaction, current)


async def setup(bot: commands.Bot):
    await bot.add_cog(CacheStats(bot))
