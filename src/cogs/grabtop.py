import discord
import src.config.subclasses
from discord.ext import commands
from discord import app_commands
from src.config import GUILD_ID
from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.coin_repository import CoinRepository
from src.utils.leaderboard import create_leaderboard_embed, create_master_embed

class GrabTop(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="grabtop", description="Display the top members in various categories")
    async def grabtop(self, interaction: discord.Interaction):
        """Displays the top members in various categories."""
        await interaction.response.defer(ephemeral=False)

        sailor_repo = SailorRepository()
        coin_repo = CoinRepository()
        guild = self.bot.get_guild(GUILD_ID)
        id_list_of_members = [member.id for member in guild.members]
                
        try:
            # Get the top 3 current members for each category
            top_voyage_count = sailor_repo.get_top_members_by_voyage_count(3, id_list_of_members)  # Top 3 by voyage count
            top_hosting_count = sailor_repo.get_top_members_by_hosting_count(3, id_list_of_members)  # Top 3 by hosting count
            
            top_carpenter = sailor_repo.get_top_members_by_subclass("carpenter", 3, id_list_of_members)  # Top 3 by carpenter points
            top_flex = sailor_repo.get_top_members_by_subclass("flex", 3, id_list_of_members)  # Top 3 by flex points
            top_cannoneer = sailor_repo.get_top_members_by_subclass("cannoneer", 3, id_list_of_members)  # Top 3 by cannoneer points
            top_helm = sailor_repo.get_top_members_by_subclass("helm", 3, id_list_of_members)  # Top 3 by helm points
            top_grenadier = sailor_repo.get_top_members_by_subclass("grenadier", 3, id_list_of_members)  # Top 3 by grenadier points
            top_field_surgeon = sailor_repo.get_top_members_by_subclass("surgeon", 3, id_list_of_members)  # Top 3 by field surgeon points

            top_coin_holder = coin_repo.get_top_coin_holders(3, id_list_of_members) #Top 3 Coin Holders

           # Get lists of members with over 50 points in ALL specified subclasses
            subclass_masters = []
            for member in interaction.guild.members:
                member_role_ids = [role.id for role in member.roles]
                if all(role_id in member_role_ids for role_id in [src.config.MASTER_CANNONEER.role_id, src.config.MASTER_HELM.role_id, src.config.MASTER_CARPENTER.role_id, src.config.MASTER_FLEX.role_id]):
                   subclass_masters.append((int(member.id)))
                   
            # Create embeds for each category
            print(f"Subclass Masters: {subclass_masters}")
            print(f"Helm: {top_helm}")
            embeds = [
                create_leaderboard_embed(self.bot, GUILD_ID, top_voyage_count, title="Top Voyage Count"),
                create_leaderboard_embed(self.bot, GUILD_ID, top_hosting_count, title="Top Hosting Count"),
                create_leaderboard_embed(self.bot, GUILD_ID, top_carpenter, title="Top Carpenter Points"),
                create_leaderboard_embed(self.bot, GUILD_ID, top_flex, title="Top Flex Points"),
                create_leaderboard_embed(self.bot, GUILD_ID, top_cannoneer, title="Top Cannoneer Points"),
                create_leaderboard_embed(self.bot, GUILD_ID, top_helm, title="Top Helm Points"),
                create_leaderboard_embed(self.bot, GUILD_ID, top_grenadier, title="Top Grenadier Points"),
                create_leaderboard_embed(self.bot, GUILD_ID, top_field_surgeon, title="Top Field Surgeon Points"),
                create_leaderboard_embed(self.bot, GUILD_ID, top_coin_holder, title="Most Challenge Coins"),
                create_master_embed(self.bot, GUILD_ID, subclass_masters, title="Subclass Masters")
                
            ]

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