from datetime import date, datetime, timezone
from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.config.cache import IMAGE_CACHES
from src.data.repository.streak_repository import StreakRepository
from src.security import require_any_role, Role
from src.utils.embeds import default_embed, error_embed
from src.utils.image_cache import BinaryImageCache
from src.utils.streak_utils import compute_streaks, generate_streak_calendar_image

log = getLogger(__name__)

STREAK_CALENDAR_CACHE = BinaryImageCache(IMAGE_CACHES["streak_calendar"])


class StreakCalendarView(discord.ui.View):
    def __init__(
            self,
            target: discord.Member,
            voyage_dates: list[date],
            hosted_dates: list[date],
            initial_year: int,
            initial_month: int,
    ):
        super().__init__(timeout=120)
        self.target = target
        self.voyage_dates = voyage_dates
        self.hosted_dates = hosted_dates
        self.year = initial_year
        self.month = initial_month
        self.now = datetime.now(timezone.utc).date()

        # Restriction: 24 months back
        self.min_date = date(self.now.year - 2, self.now.month, 1)

        self._update_button_states()

    def _update_button_states(self):
        # Disable Next if current month is today's month/year
        if self.year >= self.now.year and self.month >= self.now.month:
            self.next_month.disabled = True
        else:
            self.next_month.disabled = False

        # Disable Previous if we hit the 24-month limit
        if self.year <= self.min_date.year and self.month <= self.min_date.month:
            self.previous_month.disabled = True
        else:
            self.previous_month.disabled = False

    async def _update_message(self, interaction: discord.Interaction):
        self._update_button_states()
        await interaction.response.defer()
        embeds, files = await self.build_streak_content()
        await interaction.edit_original_response(embeds=embeds, attachments=files, view=self)

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary)
    async def previous_month(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.month -= 1
        if self.month == 0:
            self.month = 12
            self.year -= 1
        await self._update_message(interaction)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary)
    async def next_month(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.month += 1
        if self.month == 13:
            self.month = 1
            self.year += 1
        await self._update_message(interaction)

    async def on_timeout(self) -> None:
        """Remove buttons when the view times out."""
        # Note: We can't edit the original message here easily without an interaction,
        # but the bot will stop responding to button clicks. 
        # Standard practice is to leave them or disable them if we have the message object.
        self.stop()

    async def build_streak_content(self) -> tuple[list[discord.Embed], list[discord.File]]:
        v_curr, v_long, v_l_start, v_l_end, v_exp = compute_streaks(self.voyage_dates)
        h_curr, h_long, h_l_start, h_l_end, h_exp = compute_streaks(self.hosted_dates)

        embed = default_embed(
            title=f"Streaks — {self.target.display_name or self.target.name}",
            description=self.target.mention,
            author=False,
        )

        try:
            avatar_url = (
                self.target.guild_avatar.url if self.target.guild_avatar else self.target.avatar.url
            )
            embed.set_thumbnail(url=avatar_url)
        except AttributeError:
            pass

        # Voyage Streaks
        v_curr_val = f"{v_curr} days" if v_curr >= 2 else "No active streak"
        embed.add_field(name="⛵ Voyage Streak", value=v_curr_val, inline=True)

        v_long_val = f"{v_long} days" if v_long > 0 else "No streak yet"
        if v_long > 0 and v_l_start and v_l_end:
            v_long_val += f"\n({v_l_start.strftime('%b %d')} - {v_l_end.strftime('%b %d')})"
        embed.add_field(name="🏆 Best Voyage", value=v_long_val, inline=True)

        if v_exp:
            v_ts = int(datetime(v_exp.year, v_exp.month, v_exp.day, tzinfo=timezone.utc).timestamp())
            v_exp_val = f"<t:{v_ts}:R>"
        else:
            v_exp_val = "N/A"
        embed.add_field(name="⏳ Voyage Expiry", value=v_exp_val, inline=True)

        # Hosting Streaks
        h_curr_val = f"{h_curr} days" if h_curr >= 2 else "No active streak"
        embed.add_field(name="⚓ Hosting Streak", value=h_curr_val, inline=True)

        h_long_val = f"{h_long} days" if h_long > 0 else "No streak yet"
        if h_long > 0 and h_l_start and h_l_end:
            h_long_val += f"\n({h_l_start.strftime('%b %d')} - {h_l_end.strftime('%b %d')})"
        embed.add_field(name="🏆 Best Hosting", value=h_long_val, inline=True)

        if h_exp:
            h_ts = int(datetime(h_exp.year, h_exp.month, h_exp.day, tzinfo=timezone.utc).timestamp())
            h_exp_val = f"<t:{h_ts}:R>"
        else:
            h_exp_val = "N/A"
        embed.add_field(name="⏳ Hosting Expiry", value=h_exp_val, inline=True)

        # Caching and generating image
        img_payload = {
            "target_id": self.target.id,
            "year": self.year,
            "month": self.month,
            "v_dates": [d.isoformat() for d in self.voyage_dates if d.year == self.year and d.month == self.month],
            "h_dates": [d.isoformat() for d in self.hosted_dates if d.year == self.year and d.month == self.month],
            "version": 2  # Incremented for color/logic changes
        }

        img_data = await STREAK_CALENDAR_CACHE.get_or_create_bytes_async(
            img_payload,
            lambda: generate_streak_calendar_image(self.voyage_dates, self.hosted_dates, self.year, self.month)
        )

        file = STREAK_CALENDAR_CACHE.to_discord_file(img_data, filename="activity_cal.png")
        embed.set_image(url="attachment://activity_cal.png")

        return [embed], [file]


class Streak(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="streak", description="View voyage and hosting streaks for a member")
    @app_commands.describe(target="The member to check (defaults to yourself)")
    @require_any_role(Role.JE)
    async def streak(
            self,
            interaction: discord.Interaction,
            target: discord.Member = None,
    ):
        await interaction.response.defer()

        if target is None:
            target = interaction.user

        streak_repo = StreakRepository()
        try:
            voyage_dates = streak_repo.get_voyage_activity_dates(target.id)
            hosted_dates = streak_repo.get_hosted_activity_dates(target.id)
        except Exception as e:
            log.error("Error fetching streak data for %s: %s", target.id, e)
            await interaction.followup.send(embed=error_embed(exception=e), ephemeral=True)
            return
        finally:
            streak_repo.close_session()

        now = datetime.now(timezone.utc).date()
        view = StreakCalendarView(target, voyage_dates, hosted_dates, now.year, now.month)
        embeds, files = await view.build_streak_content()

        await interaction.followup.send(embeds=embeds, files=files, view=view)

    @streak.error
    async def streak_error(self, interaction: discord.Interaction, error: commands.CommandError):
        log.error("Error in streak command: %s", error)
        if isinstance(error, app_commands.errors.MissingAnyRole):
            await interaction.followup.send(
                embed=error_embed(
                    title="Missing Permissions",
                    description="You do not have the required permissions to use this command.",
                    footer=False,
                ),
                ephemeral=True,
            )
        else:
            await interaction.followup.send(embed=error_embed(exception=error), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Streak(bot))
