import logging
from typing import Union

import discord
from discord import app_commands
from discord.ext import commands

from src.config.abbreviations import ABBREVIATION_CATEGORIES, RANK_ABBREVIATIONS, MISC_ABBREVIATIONS, \
    NAVY_ENLISTED_RANKS_ABBREVIATIONS, MARINE_ENLISTED_RANKS_ABBREVIATIONS, NAVY_OFFICER_RANKS_ABBREVIATIONS, \
    MARINE_OFFICER_RANKS_ABBREVIATIONS, SPD_ABBREVIATIONS
from src.config.ranks_roles import JE_AND_UP
from src.data.structs import Abbreviation, RankAbbreviation
from src.utils.embeds import error_embed, default_embed

log = logging.getLogger(__name__)

async def get_abbreviation(abbreviation: str) -> Abbreviation or None:
    for category in ABBREVIATION_CATEGORIES:
        for abbr in category:
            if abbr.abbreviation == abbreviation:
                return abbr
    return None

async def get_all_abbreviations() -> list[Abbreviation]:
    all_abbreviations = []
    for category in ABBREVIATION_CATEGORIES:
        all_abbreviations.extend([abbreviation for abbreviation in category])
    return all_abbreviations

async def abbreviation_autocomplete(interaction: discord.Interaction, current_input: str) -> list[app_commands.Choice]:
    choices: list[app_commands.Choice] = []
    for abbreviation in await get_all_abbreviations():
        if current_input == "":
            choices.append(app_commands.Choice(name=str(abbreviation.abbreviation), value=str(abbreviation.abbreviation)))
            continue
        elif abbreviation.abbreviation.lower().startswith(current_input.lower()):
            choices.append(app_commands.Choice(name=str(abbreviation.abbreviation), value=str(abbreviation.abbreviation)))
    return choices[:25]


class Abbreviation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="abbreviations", description="Get the meaning of a abbreviation.")
    @app_commands.autocomplete(abbreviation=abbreviation_autocomplete)
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def abbreviations(self, interaction: discord.Interaction, abbreviation: str = None):
        # If abbreviation is given, return the meaning of the abbreviation
        if abbreviation:
            abbreviation_meaning: Union[Abbreviation, RankAbbreviation] = await get_abbreviation(abbreviation)
            if abbreviation_meaning:

                embed = default_embed(
                    title="Abbreviation",
                    description=f"The abbreviation `{abbreviation_meaning.abbreviation}` stands for `{abbreviation_meaning.meaning}`."
                )
                additional_context = ""
                if isinstance(abbreviation_meaning, RankAbbreviation) and abbreviation_meaning.associated_rank:
                    additional_context += f"{abbreviation_meaning.associated_rank.rank_context.short_description} \n"
                    additional_context += "\u200b\n"
                    additional_context += f"More information about this role can be found in the sailors handbook: \n {abbreviation_meaning.associated_rank.rank_context.embed_url}."
                    pass

                if len(additional_context) > 0:
                    embed.add_field(name="Additional context", value=additional_context, inline=False)
                await interaction.response.send_message(embed=embed)
                return

            await interaction.response.send_message(embed=error_embed("Abbreviation not found", f"The abbreviation `{abbreviation}` was not found."))
            return

        embed = default_embed(
            title="Abbreviations",
            description="Here is a list of all the abbreviations and their meanings."
        )
        abbreviations_category_map = {
            "Navy Enlisted": NAVY_ENLISTED_RANKS_ABBREVIATIONS,
            "Marine Enlisted" : MARINE_ENLISTED_RANKS_ABBREVIATIONS,
            "spacer1" : [],
            "Navy Officers": NAVY_OFFICER_RANKS_ABBREVIATIONS,
            "Marine Officers": MARINE_OFFICER_RANKS_ABBREVIATIONS,
            "spacer2": [],
            "SPD Abbreviations": SPD_ABBREVIATIONS,
            "Miscellaneous Abbreviations": MISC_ABBREVIATIONS,
        }
        for category in abbreviations_category_map:
            abbreviations = []
            for abbreviation in abbreviations_category_map[category]:
                abbreviations.append(f"`{abbreviation.abbreviation}` - {abbreviation.meaning}")
            if abbreviations:
                embed.add_field(name=category, value="\n".join(abbreviations), inline=True)
            else:
                embed.add_field(name="\u200b", value="\u200b", inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Abbreviation(bot))