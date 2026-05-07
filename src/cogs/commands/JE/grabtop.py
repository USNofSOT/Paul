import logging

import discord
from config.subclasses import SUBCLASS_AWARDS
from discord import app_commands
from discord.ext import commands

from src.config import GUILD_ID
from src.data.repository.coin_repository import CoinRepository
from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.streak_repository import StreakRepository
from src.security import require_any_role, Role
from src.utils.leaderboard import create_leaderboard_embed, create_master_embed, create_subclass_leaderboard_embed, \
    create_dual_leaderboard_embed, create_triple_leaderboard_embed

log = logging.getLogger(__name__)


class GrabTop(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="grabtop", description="Display the top members in various categories")
    @app_commands.describe(category="Select a specific category to display, or leave blank for all")
    @require_any_role(Role.JE)
    @app_commands.choices(category=[
        app_commands.Choice(name="Voyages and Hosting", value="voyages_hosting"),
        app_commands.Choice(name="Subclass Points", value="subclass_points"),
        app_commands.Choice(name="Coins", value="coins"),
        app_commands.Choice(name="Subclass Masters", value="subclass_masters"),
        app_commands.Choice(name="Streaks", value="streaks"),
    ])
    @app_commands.choices(limit=[
        app_commands.Choice(name="1", value=1),
        app_commands.Choice(name="2", value=2),
        app_commands.Choice(name="3", value=3),
        app_commands.Choice(name="4", value=4),
        app_commands.Choice(name="5", value=5),
        app_commands.Choice(name="6", value=6),
        app_commands.Choice(name="7", value=7),
        app_commands.Choice(name="8", value=8),
        app_commands.Choice(name="9", value=9),
        app_commands.Choice(name="10", value=10)
    ])
    async def grabtop(self, interaction: discord.Interaction, category: str = None, limit: int = 3):
        """Displays the top members in various categories."""
        await interaction.response.defer(ephemeral=False)

        sailor_repo = SailorRepository()
        hosted_repo = HostedRepository()
        coin_repo = CoinRepository()
        streak_repo = StreakRepository()

        guild = self.bot.get_guild(GUILD_ID) or interaction.guild
        if guild:
            id_list_of_members = [member.id for member in guild.members]
        else:
            id_list_of_members = []

        if not id_list_of_members:
            log.warning("GrabTop: No members found in guild cache.")
            await interaction.followup.send("Unable to fetch guild members. Please try again.", ephemeral=True)
            return

        try:
            # Get the top members for each category
            top_voyage_count = sailor_repo.get_top_members_by_voyage_count(limit, id_list_of_members)  # Top voyage count
            top_hosting_count = sailor_repo.get_top_members_by_hosting_count(limit, id_list_of_members)  # Top hosting count
            top_vp_count = hosted_repo.get_top_members_by_public_service_count(limit, id_list_of_members) # Top public service count
            
            top_carpenter = sailor_repo.get_top_members_by_subclass("carpenter", limit, id_list_of_members)  # Top carpenter points
            top_flex = sailor_repo.get_top_members_by_subclass("flex", limit, id_list_of_members)  # Top flex points
            top_cannoneer = sailor_repo.get_top_members_by_subclass("cannoneer", limit, id_list_of_members)  # Top cannoneer points
            top_helm = sailor_repo.get_top_members_by_subclass("helm", limit, id_list_of_members)  # Top helm points
            top_grenadier = sailor_repo.get_top_members_by_subclass("grenadier", limit, id_list_of_members)  # Top grenadier points
            top_field_surgeon = sailor_repo.get_top_members_by_subclass("surgeon", limit, id_list_of_members)  # Top field surgeon points

            top_coin_holder = coin_repo.get_top_coin_holders(limit, id_list_of_members) #Top 3 Coin Holders

           # Get lists of members with over 25 points in ALL specified subclasses
            subclass_masters = []
            master_role_ids = [award.role_id for award in SUBCLASS_AWARDS.masters]
            for member in interaction.guild.members:
                member_role_ids = [role.id for role in member.roles]
                if all(role_id in member_role_ids for role_id in master_role_ids):
                   subclass_masters.append((int(member.id)))
                   
            # Create embeds for each category
            embeds = []
            log.info(f"GrabTop: category={category}, limit={limit}, member_count={len(id_list_of_members)}")

            # Voyages and Hosting Category
            if category is None or category == "voyages_hosting":
                embeds.append(create_triple_leaderboard_embed(self.bot, GUILD_ID, top_voyage_count, "Top Voyage Count", top_hosting_count, "Top Hosting Count", top_vp_count, "Top Public Service Count"))
                log.info("GrabTop: Fetching voyages_hosting data")
                top_v = sailor_repo.get_top_members_by_voyage_count(limit, id_list_of_members)
                top_h = sailor_repo.get_top_members_by_hosting_count(limit, id_list_of_members)
                top_vp = hosted_repo.get_top_members_by_public_service_count(limit, id_list_of_members)

                embeds.append(create_triple_leaderboard_embed(
                    self.bot, guild.id,
                    top_v, "Top Voyage Count",
                    top_h, "Top Hosting Count",
                    top_vp, "Top Public Service Count"
                ))

            # Subclass Points Category
            if category is None or category == "subclass_points":
                log.info("GrabTop: Fetching subclass_points data")
                top_carpenter = sailor_repo.get_top_members_by_subclass("carpenter", limit, id_list_of_members)
                top_flex = sailor_repo.get_top_members_by_subclass("flex", limit, id_list_of_members)
                top_cannoneer = sailor_repo.get_top_members_by_subclass("cannoneer", limit, id_list_of_members)
                top_helm = sailor_repo.get_top_members_by_subclass("helm", limit, id_list_of_members)
                top_grenadier = sailor_repo.get_top_members_by_subclass("grenadier", limit, id_list_of_members)
                top_field_surgeon = sailor_repo.get_top_members_by_subclass("surgeon", limit, id_list_of_members)

                embeds.append(create_subclass_leaderboard_embed(
                    self.bot, guild.id,
                    top_helm, top_flex, top_cannoneer,
                    top_carpenter, top_field_surgeon, top_grenadier
                ))

            # Coins Category
            if category is None or category == "coins":
                log.info("GrabTop: Fetching coins data")
                top_coin_holder = coin_repo.get_top_coin_holders(limit, id_list_of_members)
                embeds.append(create_leaderboard_embed(
                    self.bot, guild.id, top_coin_holder, title="Most Challenge Coins"
                ))

            # Subclass Masters Category
            if category is None or category == "subclass_masters":
                log.info("GrabTop: Fetching subclass_masters data")
                subclass_masters = []
                master_role_ids = [award.role_id for award in SUBCLASS_AWARDS.masters]
                for member in guild.members:
                    member_role_ids = [role.id for role in member.roles]
                    if all(role_id in member_role_ids for role_id in master_role_ids):
                        subclass_masters.append(int(member.id))

                embeds.append(create_master_embed(
                    self.bot, guild.id, subclass_masters, title="Subclass Masters"
                ))

            # Streaks Category (Unified Hall of Fame)
            if category is None or category == "streaks":
                log.info("GrabTop: Fetching consolidated streaks data")

                # Current
                top_v_raw = streak_repo.get_top_voyage_streaks(id_list_of_members, limit)
                top_v_curr = [(mid, f"{length} days") for mid, length in top_v_raw]

                top_h_raw = streak_repo.get_top_hosted_streaks(id_list_of_members, limit)
                top_h_curr = [(mid, f"{length} days") for mid, length in top_h_raw]

                # All-Time
                top_v_at_raw = streak_repo.get_top_voyage_streaks_all_time(id_list_of_members, limit)
                top_v_at = [(mid, f"{length} days") for mid, length in top_v_at_raw]

                top_h_at_raw = streak_repo.get_top_hosted_streaks_all_time(id_list_of_members, limit)
                top_h_at = [(mid, f"{length} days") for mid, length in top_h_at_raw]

                # Show Current in one dual embed
                embeds.append(create_dual_leaderboard_embed(
                    self.bot, guild.id,
                    top_v_curr, "⛵ 🔥 Current Voyage Streaks",
                    top_h_curr, "⚓ 🔥 Current Hosting Streaks"
                ))

                # Show All-Time in another dual embed
                embeds.append(create_dual_leaderboard_embed(
                    self.bot, guild.id,
                    top_v_at, "🏆 🔥 All-Time Voyage Streaks",
                    top_h_at, "🏆 🔥 All-Time Hosting Streaks"
                ))

            # Send all collected embeds
            if embeds:
                log.info(f"GrabTop: Sending {len(embeds)} embeds")
                for embed in embeds:
                    await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("No data found for the selected category.", ephemeral=True)

        except Exception as e:
            await interaction.followup.send("An error occurred while fetching the data.", ephemeral=True)
            log.error(f"GrabTop: Failed to fetch and display data: {e}", exc_info=True)
            raise e
        finally:
            sailor_repo.close_session()
            hosted_repo.close_session()
            coin_repo.close_session()
            streak_repo.close_session()


async def setup(bot: commands.Bot):
    await bot.add_cog(GrabTop(bot))
