from logging import getLogger

import discord
from discord.ext import commands

from src.config.main_server import BC_BOA
from src.config.ranks_roles import BOA_ROLE
from src.data import ModNotes
from src.data.repository.modnote_repository import ModNoteRepository

log = getLogger(__name__)

class DumpNotes(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="dumpnotes")
    @commands.has_role(BOA_ROLE)
    async def dump_notes(self, ctx: commands.Context):
        if ctx.channel.id != BC_BOA:
            await ctx.channel.send(
                embed=discord.Embed(
                    title="Error",
                    description="You can only run this command in the designated BOA channel.",
                    color=discord.Color.red()
                ))
            return


        mod_note_repository = ModNoteRepository()
        session = mod_note_repository.get_session()
        notes: [ModNotes] = session.query(ModNotes).all()
        session.close()

        # Send the csv file to the user
        with open("modnotes.csv", "w") as f:
            f.write("id,target_id,mod_id,note,date,hidden\n")
            for note in notes:
                f.write(f"{note.id},{note.target_id},{note.moderator_id},{note.note},{note.note_time},{note.hidden}\n")

        await ctx.send(file=discord.File("modnotes.csv"))

    @dump_notes.error
    async def dump_notes_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRole):
            await ctx.send(
                embed=discord.Embed(
                    title="Not Allowed",
                    description="You do not have the correct role to run this command.",
                    color=discord.Color.red()
                ))
        else:
            log.error(f"Error running dump_notes command: {error}")

async def setup(bot: commands.Bot):
    await bot.add_cog(DumpNotes(bot))
