from __future__ import annotations

from logging import getLogger
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from src.config import (
    CACHE_CATEGORY_METADATA,
    IMAGE_CACHES,
    MEMORY_CACHES,
    group_image_caches_by_category,
    group_memory_caches_by_category,
)
from src.data.repository.cache_stats_repository import CacheStatsRepository
from src.security import require_any_role, Role, resolve_effective_roles
from src.utils.embeds import default_embed, error_embed
from src.utils.image_cache import clear_cached_items, get_cached_item_count

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
        "directory": getattr(cache_config, "directory", "In-Memory"),
        "extension": getattr(cache_config, "extension", "N/A"),
        "version": getattr(cache_config, "version", 1),
        "ttl": format_cache_ttl(cache_config.ttl_seconds),
        "max_items": cache_config.max_items,
        "cached_items": (
            get_cached_item_count(cache_config)
            if hasattr(cache_config, "directory")
            else "N/A"
        ),
        **stats,
    }


def build_cache_snapshots() -> dict[str, dict[str, Any]]:
    stored_stats = fetch_stored_cache_stats()
    all_configs = {**IMAGE_CACHES, **MEMORY_CACHES}
    return {
        cache_name: build_cache_snapshot(
            cache_config,
            stored_stats.get(cache_name, _empty_cache_stats()),
        )
        for cache_name, cache_config in all_configs.items()
    }


def build_cache_report_embeds(scope: str | None) -> list[discord.Embed]:
    snapshots = build_cache_snapshots()

    if scope:
        scope_key = scope.lower()
        if scope_key in snapshots:
            return build_single_cache_embeds(scope_key)

        # Check if it's a category
        grouped_image_caches = group_image_caches_by_category()
        grouped_memory_caches = group_memory_caches_by_category()
        if scope_key in grouped_image_caches or scope_key in grouped_memory_caches:
            # For category scope, we still do the 6-per-page logic but filtered
            image_members = grouped_image_caches.get(scope_key, {})
            memory_members = grouped_memory_caches.get(scope_key, {})
            all_members = list(image_members.keys()) + list(memory_members.keys())
            return _build_paginated_embeds([snapshots[name] for name in all_members],
                                           title_prefix=f"{category_title(scope_key)} ")

    # Global scope (all caches)
    return _build_paginated_embeds(list(snapshots.values()))


def _build_paginated_embeds(cache_list: list[dict[str, Any]], title_prefix: str = "") -> list[discord.Embed]:
    # Sort by name for consistency
    cache_list.sort(key=lambda x: x["name"])
    
    total_items = 0
    total_requests = 0
    total_hits = 0
    total_misses = 0

    # 1. Build Overview Summary
    summary_embed = default_embed(
        title=f"{title_prefix}Cache Overview",
        description="Global traffic and retention report.",
    )

    # Calculate totals first
    for item in cache_list:
        total_requests += item["request_count"]
        total_hits += item["cache_hit_count"]
        total_misses += item["cache_miss_count"]
        if isinstance(item["cached_items"], int):
            total_items += item["cached_items"]

    overall_hit_rate = (
        round((total_hits / total_requests) * 100, 2)
        if total_requests
        else 0
    )

    summary_embed.add_field(
        name="Global Totals",
        value=(
            f"Total Caches: **{len(cache_list)}**\n"
            f"Cached Items: **{total_items}**\n"
            f"Requests: **{total_requests}**\n"
            f"Hits / Misses: **{total_hits} / {total_misses}**\n"
            f"Overall Hit Rate: **{overall_hit_rate:.2f}%**"
        ),
        inline=False,
    )

    # 2. Build Paginated Details (9 per page)
    detail_embeds: list[discord.Embed] = []
    PAGE_SIZE = 9
    for i in range(0, len(cache_list), PAGE_SIZE):
        page_items = cache_list[i: i + PAGE_SIZE]
        page_num = (i // PAGE_SIZE) + 1

        embed = default_embed(
            title=f"{title_prefix}Cache Details (Page {page_num})",
            description="Per-cache performance metrics.",
        )

        for item in page_items:
            items_str = (
                f"Items: **{item['cached_items']}/{item['max_items']}**"
                if item['cached_items'] != "N/A"
                else f"Max: **{item['max_items']}**"
            )
            embed.add_field(
                name=f"{item['name']}",
                value=(
                    f"Traffic: **{item['cache_hit_count']} / {item['cache_miss_count']}**\n"
                    f"Hit Rate: **{item['cached_percent']:.2f}%**\n"
                    f"{items_str} • TTL: **{item['ttl']}**"
                ),
                inline=True,
            )
        detail_embeds.append(embed)

    return [summary_embed, *detail_embeds]


def build_single_cache_embeds(cache_name: str) -> list[discord.Embed]:
    item = build_cache_snapshots()[cache_name]

    overview_embed = default_embed(
        title=f"Cache Report: {cache_name}",
        description=(
            f"{category_title(item['category'])}\n"
            f"Type: **{'In-Memory' if item['directory'] == 'In-Memory' else 'On-Disk'}**\n"
            f"Directory: `{item['directory']}`"
        ),
    )
    overview_embed.add_field(
        name="Traffic",
        value=(
            f"Requests: **{item['request_count']}**\n"
            f"Hits / Misses: **{item['cache_hit_count']} / {item['cache_miss_count']}**\n"
            f"Hit Rate: **{item['cached_percent']:.2f}%**"
        ),
        inline=True,
    )

    retention_value = (
        f"Items: **{item['cached_items']}/{item['max_items']}**\n"
        f"TTL: **{item['ttl']}**\n"
        f"Extension: **{item['extension']}**"
    ) if item['cached_items'] != "N/A" else (
        f"Max Items: **{item['max_items']}**\n"
        f"TTL: **{item['ttl']}**"
    )

    overview_embed.add_field(
        name="Retention",
        value=retention_value,
        inline=True,
    )
    overview_embed.add_field(
        name="Configuration",
        value=f"Version: **{item['version']}**\nNamespace: `{item['name']}`",
        inline=True,
    )

    if item['directory'] != "In-Memory":
        janitor_embed = default_embed(
            title=f"Janitor Report: {cache_name}",
            description="Cleanup history for this persistent cache.",
        )
        janitor_embed.add_field(
            name="Cumulative Totals",
            value=(
                f"Runs: **{item['janitor_run_count']}**\n"
                f"Expired removed: **{item['janitor_removed_expired_count']}**\n"
                f"Overflow removed: **{item['janitor_removed_overflow_count']}**"
            ),
            inline=True,
        )
        janitor_embed.add_field(
            name="Last Run Result",
            value=(
                f"Expired removed: **{item['janitor_last_removed_expired']}**\n"
                f"Overflow removed: **{item['janitor_last_removed_overflow']}**\n"
                f"Remaining items: **{item['janitor_last_remaining_items']}**"
            ),
            inline=True,
        )
        return [overview_embed, janitor_embed]

    return [overview_embed]


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
    def __init__(self, scope: str | None, embeds: list[discord.Embed]):
        super().__init__(timeout=300)
        self.scope = scope
        self.embeds = embeds
        self.current_page = 0
        self.message: discord.Message | None = None

        self.add_item(CacheStatsControls(self))
        self._update_button_states()

    def _update_button_states(self):
        self.prev_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page == len(self.embeds) - 1

    async def _update_message(self, interaction: discord.Interaction):
        self._update_button_states()
        embed = self.embeds[self.current_page]
        embed.set_footer(text=f"Page {self.current_page + 1} of {len(self.embeds)}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        await self._update_message(interaction)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self._update_message(interaction)

    async def refresh_message(self) -> None:
        if self.message is None:
            return
        self.embeds = build_cache_report_embeds(self.scope)
        self.current_page = min(self.current_page, len(self.embeds) - 1)
        self._update_button_states()

        embed = self.embeds[self.current_page]
        embed.set_footer(text=f"Page {self.current_page + 1} of {len(self.embeds)}")
        await self.message.edit(embed=embed, view=self)


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

        view = CacheStatsReportView(scope, embeds)

        # Set footer for initial page
        first_embed = embeds[0]
        first_embed.set_footer(text=f"Page 1 of {len(embeds)}")
        
        message = await interaction.followup.send(
            embed=first_embed,
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
        grouped_image_caches = group_image_caches_by_category()
        grouped_memory_caches = group_memory_caches_by_category()
        all_categories = set(grouped_image_caches.keys()) | set(grouped_memory_caches.keys())

        options = [
            *all_categories,
            *IMAGE_CACHES.keys(),
            *MEMORY_CACHES.keys(),
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
