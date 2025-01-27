import logging

import discord
from config import GUILD_ID, NSC_ROLES, VOYAGE_LOGS
from config.emojis import ANCIENT_COINS_EMOJI, DOUBLOONS_EMOJI, GOLD_EMOJI
from config.ships import SHIPS
from data import Subclasses
from data.repository.hosted_repository import HostedRepository
from data.repository.subclass_repository import SubclassRepository
from data.repository.voyage_repository import VoyageRepository
from discord import Message
from discord.ext import commands
from utils.embeds import default_embed, error_embed
from utils.process_voyage_log import Process_Voyage_Log
from utils.remove_voyage_log import remove_voyage_log_data
from utils.ship_utils import convert_to_ordinal

log = logging.getLogger(__name__)

async def build_embed(self, voyage_log_id: str = None) -> discord.Embed:
    if not voyage_log_id:
        return error_embed(
                title="Voyage Log Information",
                description="Please provide a Voyage Log ID."
            )

    if not voyage_log_id.isnumeric():
        return error_embed(
                title="Voyage Log Information",
                description=f"Voyage Log ID: {voyage_log_id} is not a valid number."
            )

    hosted_repository = HostedRepository()
    hosted = hosted_repository.get_host_by_log_id(int(voyage_log_id))
    hosted_repository.close_session()

    if not hosted:
        embed = error_embed(
            title="Voyage Log Information",
            description=f"Voyage Log ID: {voyage_log_id} not found in the database. \n https://discord.com/channels/{GUILD_ID}/{VOYAGE_LOGS}/{voyage_log_id}"
        )
    else:
        embed = default_embed(
            title=f"Voyage Log Information `{voyage_log_id}`",
            description=f"https://discord.com/channels/{GUILD_ID}/{VOYAGE_LOGS}/{voyage_log_id} by <@{hosted.target_id}>"
        )

        ship_emoji = None
        for ship in SHIPS:
            if ship.name == hosted.ship_name:
                ship_emoji = ship.emoji
                break

        if ship_emoji:
            embed.add_field(name="Ship", value=f"{ship_emoji} {hosted.ship_name if hosted.ship_name else 'N/A'}", inline=True)
        else:
            embed.add_field(name="Ship", value=hosted.ship_name if hosted.ship_name else "N/A", inline=True)

        embed.add_field(name="Auxiliary Ship",
                        value=hosted.auxiliary_ship_name if hosted.auxiliary_ship_name else "N/A", inline=True)

        embed.add_field(name="Voyage Count",
                        value=convert_to_ordinal(hosted.ship_voyage_count) if hosted.ship_voyage_count else "N/A",
                        inline=True)

        embed.add_field(name="Voyage Type", value=hosted.voyage_type.name.capitalize() if hosted.voyage_type else "N/A", inline=True)
        embed.add_field(name="Gold", value=f"{GOLD_EMOJI} {hosted.gold_count:,}", inline=True)
        embed.add_field(name="Doubloons", value=f"{DOUBLOONS_EMOJI} {hosted.doubloon_count:,}", inline=True)

        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Ancient Coins", value=f"{ANCIENT_COINS_EMOJI} {hosted.ancient_coin_count:,}" if hosted.ancient_coin_count else "N/A", inline=True)
        embed.add_field(name="Fish", value=f":fish: {hosted.fish_count:,}" if hosted.fish_count else "N/A", inline=True)


    voyage_repository = VoyageRepository()
    voyages = voyage_repository.get_voyages_by_log_id(int(voyage_log_id))
    voyage_repository.close_session()

    if voyages:
        voyage_txt = ""
        for voyage in voyages:
            voyage_txt += f"<@{voyage.target_id}> @ <t:{int(voyage.log_time.timestamp())}>\n"
        embed.add_field(name="Voyagers", value=voyage_txt, inline=False)

    subclass_repository = SubclassRepository()
    subclasses: [Subclasses] = subclass_repository.entries_for_log_id(int(voyage_log_id))
    subclass_repository.close_session()

    if subclasses:
        subclass_txt = ""
        for subclass in subclasses:
            subclass_txt += f"<@{subclass.target_id}> {subclass.subclass_count}x {subclass.subclass.name.capitalize()} @ <t:{int(subclass.log_time.timestamp())}>\n"
        embed.add_field(name="Subclasses", value=subclass_txt, inline=False)

    log_channel = self.bot.get_channel(VOYAGE_LOGS)
    try:
        log_message: Message or None = await log_channel.fetch_message(int(voyage_log_id))
    except discord.errors.NotFound:
        log_message = None

    if log_message:
        embed.add_field(name="Created at", value=f"<t:{int(log_message.created_at.timestamp())}>", inline=True)
        if log_message.edited_at:
            embed.add_field(name="Edited at", value=f"<t:{int(log_message.edited_at.timestamp())}>", inline=True)

    return embed

class VoyageInformationView(discord.ui.View):
    def __init__(self, bot, voyage_log_id):
        super().__init__()
        self.bot = bot
        self.voyage_log_id = voyage_log_id


    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⬅️")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Get the previous voyage log from the channel relative to the current voyage log.
        """
        channel = self.bot.get_channel(VOYAGE_LOGS)
        current_message = await channel.fetch_message(self.voyage_log_id)
        messages = [msg async for msg in channel.history(limit=1, before=current_message)]
        if messages:
            # Update the original message
            await interaction.message.edit(embed=await build_embed(self, str(messages[0].id)), view=self)
            self.voyage_log_id = str(messages[0].id)
            # Acknowledge the interaction
            await interaction.response.defer(ephemeral=True)
        else:
            await interaction.response.send_message(embed=error_embed(
                title="Voyage Log Information",
                description="No more messages found in the channel."
            ), ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="🔄")
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Refresh the current voyage log information.
        """
        # Update the original message
        await interaction.message.edit(embed=await build_embed(self, self.voyage_log_id), view=self)
        # Acknowledge the interaction
        await interaction.response.defer(ephemeral=True)


    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="➡️")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Get the next voyage log from the channel relative to the current voyage log.
        """
        channel = self.bot.get_channel(VOYAGE_LOGS)
        current_message = await channel.fetch_message(self.voyage_log_id)
        messages = [msg async for msg in channel.history(limit=1, after=current_message)]
        if messages:
            # Update the original message
            await interaction.message.edit(embed=await build_embed(self, str(messages[0].id)), view=self)
            self.voyage_log_id = str(messages[0].id)
            # Acknowledge the interaction
            await interaction.response.defer(ephemeral=True)
        else:
            await interaction.response.send_message(embed=error_embed(
                title="Voyage Log Information",
                description="No more messages found in the channel."
            ), ephemeral=True)

    @discord.ui.select(
        placeholder="Select an option...",
        options=[
            discord.SelectOption(label="🆕 Initialize Data", value="initialize"),
            discord.SelectOption(label="🗑️ Delete Data", value="delete"),
            discord.SelectOption(label="🗑️ Delete Subclasses", value="delete_subclasses"),
            discord.SelectOption(label="📚 Process Subclasses", value="process_subclasses")
        ],
    )
    async def select_callback(self, interaction: discord.Interaction, select):
        if not [int(role.id) for role in interaction.user.roles if role.id in NSC_ROLES]:
            log.error(f"User {interaction.id} does not have permission to perform this action.")
            await interaction.response.send_message(embed=error_embed(
                title="Voyage Log Information",
                description="You do not have permission to perform this action."
            ), ephemeral=True)
            return

        if select.values[0] == "initialize":
            # Attempt to get the message
            message = await self.bot.get_channel(VOYAGE_LOGS).fetch_message(self.voyage_log_id)
            await Process_Voyage_Log.process_voyage_log(message)
        elif select.values[0] == "delete":
            hosted_repository = HostedRepository()
            voyage_repository = VoyageRepository()
            subclass_repository = SubclassRepository()
            await remove_voyage_log_data(self.bot, self.voyage_log_id, hosted_repository, voyage_repository, subclass_repository)
            hosted_repository.close_session()
            voyage_repository.close_session()
            subclass_repository.close_session()
        elif select.values[0] == "delete_subclasses":
            subclass_repository = SubclassRepository()
            subclass_repository.delete_all_subclass_entries_for_log_id(self.voyage_log_id)
            subclass_repository.close_session()
        elif select.values[0] == "process_subclasses":
            message = await self.bot.get_channel(VOYAGE_LOGS).fetch_message(self.voyage_log_id)
            await Process_Voyage_Log.process_voyage_log(message)
            await interaction.response.send_message("To process subclasses, please use the following command:\n"
                                                    f"```/addsubclass log_id:{self.voyage_log_id}```")

        # Update the original message
        await interaction.message.edit(embed=await build_embed(self, self.voyage_log_id), view=self)
        # Acknowledge the interaction
        await interaction.response.defer(ephemeral=True)

class VoyageInformation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @commands.command()
    @commands.has_any_role(*NSC_ROLES)
    async def voyage_information(self, context: commands.Context, voyage_log_id: str = None):
        embed = await build_embed(self, voyage_log_id)
        await context.send(embed=embed, view=VoyageInformationView(self.bot, voyage_log_id))


async def setup(bot: commands.Bot):
    await bot.add_cog(VoyageInformation(bot))  # Classname(bot)
