import discord
import src.config.subclasses
from discord.ext import commands
from discord import app_commands
from src.config import GUILD_ID
from src.config.ranks_roles import JE_AND_UP
from config.subclasses import SUBCLASS_AWARDS
from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.coin_repository import CoinRepository
from src.utils.leaderboard import create_leaderboard_embed, create_master_embed, create_subclass_leaderboard_embed, create_dual_leaderboard_embed

class GrabTop(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="grabtop", description="Display the top members in various categories")
    @app_commands.describe(category="Select a specific category to display, or leave blank for all")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    @app_commands.choices(category=[
    app_commands.Choice(name="Voyages and Hosting", value="voyages_hosting"),
    app_commands.Choice(name="Subclass Points", value="subclass_points"),
    app_commands.Choice(name="Coins", value="coins"),
    app_commands.Choice(name="Subclass Masters", value="subclass_masters")
])
    @app_commands.choices(limit=[  # Added choices for limit
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
    async def grabtop(self, interaction: discord.Interaction, category: str = None, limit: int=3):
        """Displays the top members in various categories."""
        await interaction.response.defer(ephemeral=False)

        sailor_repo = SailorRepository()
        coin_repo = CoinRepository()
        guild = self.bot.get_guild(GUILD_ID)
        id_list_of_members = [member.id for member in guild.members]
                
        try:
            # Get the top members for each category
            top_voyage_count = sailor_repo.get_top_members_by_voyage_count(limit, id_list_of_members)  # Top voyage count
            top_hosting_count = sailor_repo.get_top_members_by_hosting_count(limit, id_list_of_members)  # Top hosting count
            
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
            if category is None or category == "voyages_hosting":
                embeds.append(create_dual_leaderboard_embed(self.bot, GUILD_ID, top_voyage_count, "Top Voyage Count", top_hosting_count, "Top Hosting Count"))
            if category is None or category == "subclass_points":
                embeds.append(create_subclass_leaderboard_embed(self.bot, GUILD_ID, top_helm, top_flex, top_cannoneer, top_carpenter, top_field_surgeon, top_grenadier))
            if category is None or category == "coins":
                embeds.append(create_leaderboard_embed(self.bot, GUILD_ID, top_coin_holder, title="Most Challenge Coins"))
            if category is None or category == "subclass_masters":
                embeds.append(create_master_embed(self.bot, GUILD_ID, subclass_masters, title="Subclass Masters"))

            # Send the embeds
            for embed in embeds:
                await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send("An error occurred while fetching the data.", ephemeral=True)
            print(f"Failed to fetch and display data: {e}")
            raise e
        finally:
            sailor_repo.close_session()
            coin_repo.close_session()

async def setup(bot: commands.Bot):
    await bot.add_cog(GrabTop(bot))