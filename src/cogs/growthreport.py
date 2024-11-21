import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands
from matplotlib import pyplot as plt

from src.config.ranks import DECKHAND
from src.config.ranks_roles import JE_AND_UP, E2_ROLES, DH_ROLES
from src.data import RoleChangeType
from src.data.repository.auditlog_repository import AuditLogRepository
from src.utils.embeds import error_embed, default_embed

log = logging.getLogger(__name__)

class GrowReport(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def get_growth_data(self, start_of_the_month, end_of_the_month):
        auditlog_repository = AuditLogRepository()

        seaman_added = auditlog_repository.get_role_changes_for_role_and_action_between_dates(
            role_id=E2_ROLES[0],
            action=RoleChangeType.ADDED,
            start_date=start_of_the_month,
            end_date=end_of_the_month
        )
        total_sailors_promoted_to_e2 = len(seaman_added)
        apprentice_removed = auditlog_repository.get_role_changes_for_role_and_action_between_dates(
            role_id=E2_ROLES[1],
            action=RoleChangeType.REMOVED,
            start_date=start_of_the_month,
            end_date=end_of_the_month
        )
        total_sailors_promoted_from_apprentice = len([apprentice for apprentice in apprentice_removed if apprentice.target_id in [seaman.target_id for seaman in seaman_added]])
        total_sailors_returned_from_deckhand = len(auditlog_repository.get_role_changes_for_role_and_action_between_dates(
            role_id=E2_ROLES[1],
            action=RoleChangeType.ADDED,
            start_date=start_of_the_month,
            end_date=end_of_the_month
        ))
        total_sailors_deck_handed = auditlog_repository.get_role_changes_for_role_and_action_between_dates(
            role_id=DH_ROLES[0],
            action=RoleChangeType.ADDED,
            start_date=start_of_the_month,
            end_date=end_of_the_month
        )
        total_sailors_deck_handed = len([deckhand for deckhand in total_sailors_deck_handed if deckhand.target_id not in [seaman.target_id for seaman in seaman_added]])

        total_sailors_banned = len(
            auditlog_repository.get_bans_changes_for_e2_or_above_and_between_dates(
                e2_or_above=True,
                start_date=start_of_the_month,
                end_date=end_of_the_month
            )
        )
        total_sailors_departed = len(
            auditlog_repository.get_leave_changes_for_e2_or_above_and_between_dates(
                e2_or_above=True,
                start_date=start_of_the_month,
                end_date=end_of_the_month
            )
        )

        auditlog_repository.close_session()

        return {
            "total_sailors_promoted_to_e2": total_sailors_promoted_to_e2,
            "total_sailors_promoted_from_apprentice": total_sailors_promoted_from_apprentice,
            "total_sailors_returned_from_deckhand": total_sailors_returned_from_deckhand,
            "total_sailors_deck_handed": total_sailors_deck_handed,
            "total_sailors_banned": total_sailors_banned,
            "total_sailors_departed": total_sailors_departed,
            "gain": (total_sailors_promoted_to_e2-total_sailors_promoted_from_apprentice) + total_sailors_promoted_from_apprentice,
            "loss": total_sailors_deck_handed + total_sailors_departed + total_sailors_banned
        }

    async def get_barchart_past_6_months(self):
        embed = default_embed(title="Growth report", description="Showing growth report for the past 6 months.")

        months = 6
        plt.figure(figsize=(15, 12))

        for i in range(months):
            start_of_the_month = datetime(datetime.now().year, datetime.now().month-i, 1)
            end_of_the_month = datetime(datetime.now().year, datetime.now().month-i+1, 1) - timedelta(days=1)
            data = self.get_growth_data(start_of_the_month, end_of_the_month)
            plt.bar(start_of_the_month.strftime("%b %Y"), data["gain"] - data["loss"], label=f"{start_of_the_month.strftime('%b %Y')}")

        plt.xlabel("Date")
        plt.ylabel("Net Growth")

        plt.legend()
        file_path = "./growth_bar_chart.png"
        plt.savefig(file_path)
        plt.close()

        with open(file_path, 'rb') as file:
            discord_file = discord.File(file)
            embed.set_image(url="attachment://growth_bar_chart.png")

        return embed, discord_file

    @app_commands.command(name="growreport", description="Get the growth report of a sailor.")
    @app_commands.describe(year="The year you want to get the growth report for.")
    @app_commands.describe(month="The month you want to get the growth report for.")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def growth_report(self, interaction: discord.Interaction, year: int = None, month: int = None):
        interaction.response.defer(ephemeral=False)

        if year is None:
            year = datetime.now().year

        if month is None:
            month = datetime.now().month

        if year < 2024 or year > datetime.now().year:
            await interaction.response.send_message(embed=error_embed(title="Error", description="Invalid year."), ephemeral=True)
            return
        if month < 1 or month > 12:
            await interaction.response.send_message(embed=error_embed(title="Error", description="Invalid month."), ephemeral=True)
            return

        start_of_the_month = datetime(year, month, 1)
        end_of_the_month = datetime(year, month + 1, 1) - timedelta(days=1)

        data = self.get_growth_data(start_of_the_month, end_of_the_month)

        embed = default_embed(title="Growth report", description=f"Showing growth report from **{start_of_the_month.strftime('%Y-%m-%d')}** to **{end_of_the_month.strftime('%Y-%m-%d')}**")

        embed.add_field(name="\u200b", value="Growth", inline=False)
        embed.add_field(name="🆕 New E2s", value=f"+{data['total_sailors_promoted_to_e2'] - data['total_sailors_promoted_from_apprentice']}", inline=True)
        embed.add_field(name="🔄 Returned E2s", value=f"+{data['total_sailors_promoted_from_apprentice']}", inline=True)

        embed.add_field(name="\u200b", value="Loss", inline=False)
        embed.add_field(name="🛠️ Deckhanded", value=f"-{data['total_sailors_deck_handed']}", inline=True)
        embed.add_field(name="🚶 Departed", value=f"-{data['total_sailors_departed']}", inline=True)
        embed.add_field(name="🚫 Banished", value=f"-{data['total_sailors_banned']}", inline=True)

        gain = (data['total_sailors_promoted_to_e2'] - data['total_sailors_promoted_from_apprentice']) + data['total_sailors_promoted_from_apprentice']
        loss = data['total_sailors_deck_handed'] + data['total_sailors_departed'] + data['total_sailors_banned']

        embed.add_field(name="\u200b", value="\u200b", inline=False) # Spacer

        embed.add_field(name="Gain/Loss", value=f"{gain}/{loss}", inline=True)
        embed.add_field(name="Net", value=f"{gain-loss}", inline=True)

        barchart_embed, discord_file = await self.get_barchart_past_6_months()

        await interaction.response.send_message(embeds=[embed, barchart_embed], files=[discord_file])

async def setup(bot: commands.Bot):
    await bot.add_cog(GrowReport(bot))