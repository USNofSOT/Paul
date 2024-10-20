import logging
import random

import discord
from discord import app_commands
from discord.ext import commands

from src.config.main_server import GUILD_ID
from src.config.ranks_roles import NCO_AND_UP_PURE, JE_AND_UP
from src.data import TopVoyagedTogether, top_voyaged_together, Subclasses, SubclassType, get_ranking, Rankings, Sailor
from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.subclass_repository import SubclassRepository
from src.data.repository.voyage_repository import VoyageRepository
from src.utils.embeds import default_embed, error_embed
from src.utils.time_utils import format_time, get_time_difference_past

log = logging.getLogger(__name__)

def calculate_percentage(part:int, total:int) -> str:
    rounded = round(part / total, 5)
    return "{:.2f}%".format(round(part / total * 100, 5))

class Voyages(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="voyages", description="Get information about the voyages you or a user has been on")
    @app_commands.describe(target="Select the user you want to get information about")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def voyages(self, interaction: discord.interactions, target: discord.Member = None):
        helm_emoji = "<:Wheel:1256589625993068665>"
        cannoneer_emoji = "<:Cannon:1256589581894025236>"
        flex_emoji = "<:Sword:1256589612202332313>"
        carpenter_emoji = "<:Planks:1256589596473692272>"

        if target is None:
            target = interaction.user

        # Prepare repository to be used
        voyage_repository = VoyageRepository()
        subclass_repository = SubclassRepository()
        sailor_repository = SailorRepository()

        # Get sailor
        sailor: Sailor = sailor_repository.get_sailor(target.id)
        if sailor.voyage_count == 0:
            await interaction.response.send_message(
                embed=error_embed("This sailor has not been on any voyages.", "This command becomes available after the sailor has been on at least one voyage."))
            return

        # Prepare information to be used in the embed
        guild = self.bot.get_guild(GUILD_ID)
        id_list_of_members = [member.id for member in guild.members]
        id_list_of_target_roles = [role.id for role in target.roles]

        # Top 3 of people that the user has voyaged the most with, this excludes people that are no longer in the server
        top_3: [TopVoyagedTogether] = top_voyaged_together(target.id, within_id_list=id_list_of_members)
        most_recent_voyage: Voyages or None = voyage_repository.get_most_recent_voyage(target.id)
        if most_recent_voyage:
            other_people_in_most_recent_voyage = voyage_repository.get_voyages_by_log_id(most_recent_voyage.log_id)
            other_people_in_most_recent_voyage = [voyage for voyage in other_people_in_most_recent_voyage if
                                                  voyage.target_id != target.id]
        subclasses_for_most_recent_voyage: [Subclasses] = subclass_repository.entries_for_log_id_and_target_id(
            most_recent_voyage.log_id, target.id)

        # Close repository used
        voyage_repository.close_session()
        subclass_repository.close_session()
        sailor_repository.close_session()


        embed = default_embed(
            title=f"Voyages",
            description=f"{target.mention}",
            author=False
        )
        try:
            avatar_url = target.guild_avatar.url if target.guild_avatar else target.avatar.url
            embed.set_thumbnail(url=avatar_url)
        except AttributeError:
            pass

        subclass_text = ""
        if most_recent_voyage and other_people_in_most_recent_voyage:
            if subclasses_for_most_recent_voyage:
                # Which main subclass the user was in the most recent voyage (Cannoneer, Carpenter, Flex, Helm)
                subclass_text = "The sailor contributed as a "
                main_subclass: Subclasses = [subclass for subclass in subclasses_for_most_recent_voyage
                                 if subclass.subclass in {SubclassType.CANNONEER, SubclassType.CARPENTER,SubclassType.FLEX, SubclassType.HELM}][0]
                if main_subclass.subclass == SubclassType.CANNONEER:
                    subclass_text += f"{cannoneer_emoji} **Cannoneer**"
                elif main_subclass.subclass == SubclassType.CARPENTER:
                    subclass_text += f"{carpenter_emoji} **Carpenter**"
                elif main_subclass.subclass == SubclassType.FLEX:
                    subclass_text += f"{flex_emoji} **Flex**"
                elif main_subclass.subclass == SubclassType.HELM:
                    subclass_text += f"{helm_emoji} **Helm**"
                subclass_text += f".\n"

                was_surgeon = any(subclass.subclass == SubclassType.SURGEON for subclass in subclasses_for_most_recent_voyage)
                if was_surgeon:
                    subclass_text += "Patching up :adhesive_bandage: **plenty** of crewmates along the way.\n"
                grenadier_points = sum(subclass.subclass_count for subclass in subclasses_for_most_recent_voyage if subclass.subclass == SubclassType.GRENADIER)
                if grenadier_points:
                    if grenadier_points == 1:
                        subclass_text += "The sailor even managed to **blow up** an enemy ship :boom:\n"
                    else:
                        subclass_text += f"**{grenadier_points}** enemy ships were blown up in the process. :exploding_head: \n"
            embed.add_field(
                name=":sailboat: Most Recent Voyage",
                value=f"Embarked on a voyage **{format_time(get_time_difference_past(most_recent_voyage.log_time))}** ago with :people_holding_hands:  **{len(other_people_in_most_recent_voyage)} others**.\n"
                      f"{subclass_text}",
            )

        if top_3:
            top_3_text = ""
            for index, top in enumerate(top_3):
                top_3_text += f"{index + 1}. <@{top.sailor_id}> - **{top.voyages_together}** voyages\n"
            embed.add_field(
                name=":trophy: Top 3 Sailors Voyaged With",
                value=top_3_text,
                inline=False
            )

        rankings: Rankings = get_ranking(target.id)
        rankings_map = {
            "surgeon": rankings.surgeon_rank,
            "voyages": rankings.voyages_rank,
            "hosted": rankings.hosted_rank,
            "carpenter": rankings.carpenter_rank,
            "flex": rankings.flex_rank,
            "cannoneer": rankings.cannoneer_rank,
            "helm": rankings.helm_rank,
            "grenadier": rankings.grenadier_rank,
        }
        rankings_points_map = {
            "surgeon": sailor.surgeon_points,
            "voyages": sailor.voyage_count,
            "hosted": sailor.hosted_count,
            "carpenter": sailor.carpenter_points,
            "flex": sailor.flex_points,
            "cannoneer": sailor.cannoneer_points,
            "helm": sailor.helm_points,
            "grenadier": sailor.grenadier_points,
        }

        # remove hosted from the rankings map if user not NCO_AND_UP
        if not any(role in id_list_of_target_roles for role in NCO_AND_UP_PURE):
            rankings_map.pop("hosted")

        highest_ranking = min(rankings_map, key=rankings_map.get)
        lowest_ranking_map = rankings_map.copy()
        lowest_ranking_map.pop("surgeon", None)
        lowest_ranking_map.pop("grenadier", None)
        lowest_ranking = max(rankings_map, key=rankings_map.get)

        points_map = rankings_points_map.copy()
        points_map.pop("hosted", None)
        points_map.pop("voyages", None)
        points_map.pop("surgeon", None)
        points_map.pop("grenadier", None)

        highest_play_rate = max(points_map, key=points_map.get)
        lowest_play_rate = min(points_map, key=points_map.get)

        fun_facts = [
            f"Is ranked **#{rankings_map[highest_ranking]}** in **{highest_ranking.capitalize()}** with **{rankings_points_map[highest_ranking]}** points.",
            f"Is ranked **#{rankings_map[lowest_ranking]}** in **{lowest_ranking.capitalize()}** with **{rankings_points_map[lowest_ranking]}** points.",
        ]

        if sum(points_map.values()) > 0:
            fun_facts.append(f"Plays {highest_play_rate.capitalize()} **{calculate_percentage(points_map[highest_play_rate], sum(points_map.values()))}** of the time.")
            fun_facts.append(f"Plays {lowest_play_rate.capitalize()} **{calculate_percentage(points_map[lowest_play_rate], sum(points_map.values()))}** of the time.")

        embed.add_field(
            name=":question: Fun Facts",
            value=random.choice(fun_facts),
        )


        await interaction.response.send_message(embed=embed)

    @voyages.error
    async def voyages_error(self, interaction: discord.interactions, error):
        await interaction.response.send_message(
            embed=error_embed("An error occurred while trying to get the voyages.", error))
        log.error(f"An error occurred while trying to get the voyages: {error}", exc_info=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Voyages(bot))
