import logging

import discord
from config import JE_AND_UP
from data.model.awards_model import AwardCategory
from data.repository.awards_repository import AwardsRepository
from discord import app_commands
from discord.ext import commands
from discord.ui import View

log = logging.getLogger(__name__)


def build_embed(
    category: AwardCategory, target: discord.Member = None
) -> discord.Embed:
    awards_repository = AwardsRepository()
    awards = awards_repository.find(filters={"category": category, "is_hidden": False})

    if target:
        embed = discord.Embed(title=f"{category} Awards for {target.display_name}")
    else:
        embed = discord.Embed(title=f"{category} Awards")
        for awards in awards:
            embed.add_field(name=awards.name, value=awards.description, inline=False)
        return embed

    awards = [
        award
        for award in awards
        if not (award.only_show_for_recipient and award.role_id != target.id)
    ]

    for award in awards:
        if award.has_award(target, awards):
            embed.add_field(
                name=":white_check_mark: " + award.name,
                value=award.description,
                inline=False,
            )
        else:
            embed.add_field(
                name=":x: " + award.name, value=award.description, inline=False
            )

    return embed


AWARDS_CATEGORIES = [category.value for category in AwardCategory]


class AwardsView(View):
    def __init__(self, target: discord.Member = None):
        super().__init__(timeout=120)
        self.awards = AWARDS_CATEGORIES
        self.target = target
        self.message = None

    @discord.ui.select(
        placeholder="Select an award category",
        options=[
            discord.SelectOption(label=award.capitalize(), value=award)
            for award in AWARDS_CATEGORIES
        ],
    )
    async def select_award_category(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        for category in AWARDS_CATEGORIES:
            if category in select.values:
                embed = build_embed(category, self.target)
                await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        try:
            log.info("Removing buttons due to timeout")
            for item in self.children:
                self.remove_item(item)
                await self.message.edit(view=self)
        except Exception as e:
            log.error("Error in on_timeout: %s", e)


class AwardsCommand(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="awards", description="List all awards")
    @app_commands.describe(target="Check award status for a specific user")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def awards(
        self, interaction: discord.Interaction, target: discord.Member = None
    ):
        await interaction.response.defer(ephemeral=False)

        embed = build_embed(AWARDS_CATEGORIES[0], target)
        view = AwardsView(target)
        await interaction.followup.send(embed=embed, view=view)
        view.message = await interaction.original_response()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AwardsCommand(bot))
