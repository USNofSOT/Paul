from config import GUILD_ID, NSC_ROLES, VOYAGE_LOGS
from config.emojis import DOUBLOONS_EMOJI, GOLD_EMOJI
from config.ships import SHIPS
from data import Subclasses
from data.repository.hosted_repository import HostedRepository
from data.repository.subclass_repository import SubclassRepository
from discord import Message
from discord.ext import commands
from utils.embeds import default_embed, error_embed


class VoyageInformation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @commands.command()
    @commands.has_any_role(*NSC_ROLES)
    async def voyage_information(self, context: commands.Context, voyage_log_id: str = None):
        if not voyage_log_id:
            await context.send(
                embed=error_embed(
                    title="Voyage Log Information",
                    description="Please provide a Voyage Log ID."
                )
            )
            return

        if not voyage_log_id.isnumeric():
            await context.send(
                embed=error_embed(
                    title="Voyage Log Information",
                    description=f"Voyage Log ID: {voyage_log_id} is not a valid number."
                )
            )
            return

        hosted_repository = HostedRepository()
        hosted = hosted_repository.get_host_by_log_id(int(voyage_log_id))
        hosted_repository.close_session()

        if not hosted:
            await context.send(embed=error_embed(
                title="Voyage Log Information",
                description=f"Voyage Log ID: {voyage_log_id} not found"
                )
            )
            return

        embed = default_embed(
            title="Voyage Log Information",
            description=f"https://discord.com/channels/{GUILD_ID}/{VOYAGE_LOGS}/{voyage_log_id} by <@{hosted.target_id}>"
        )

        ship_emoji = None
        for ship in SHIPS:
            if ship.name == hosted.ship_name:
                ship_emoji = ship.emoji
                break

        embed.add_field(name="Ship", value=f"{ship_emoji} {hosted.ship_name if hosted.ship_name else 'N/A'}", inline=True)
        embed.add_field(name="Gold", value=f"{GOLD_EMOJI} {hosted.gold_count}", inline=True)
        embed.add_field(name="Doubloons", value=f"{DOUBLOONS_EMOJI} {hosted.doubloon_count}", inline=True)

        embed.add_field(name="Auxiliary Ship", value=hosted.auxiliary_ship_name if hosted.auxiliary_ship_name else "N/A", inline=True)
        embed.add_field(name="Voyage Count", value=hosted.ship_voyage_count if hosted.ship_voyage_count else "N/A", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        subclass_repository = SubclassRepository()
        subclasses: [Subclasses] = subclass_repository.entries_for_log_id(int(voyage_log_id))
        subclass_repository.close_session()

        if subclasses:
            subclass_txt = ""
            for subclass in subclasses:
                subclass_txt += f"<@{subclass.target_id}> {subclass.subclass_count}x {subclass.subclass.name.capitalize()}\n"
            embed.add_field(name="Subclasses", value=subclass_txt, inline=False)

        log_channel = self.bot.get_channel(VOYAGE_LOGS)
        log_message: Message = await log_channel.fetch_message(int(voyage_log_id))

        if log_message:
            embed.add_field(name="Created at", value=f"<t:{int(log_message.created_at.timestamp())}>", inline=True)
            if log_message.edited_at:
                embed.add_field(name="Edited at", value=f"<t:{int(log_message.edited_at.timestamp())}>", inline=True)

        await context.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(VoyageInformation(bot))  # Classname(bot)
