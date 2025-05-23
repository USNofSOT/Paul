from discord import app_commands
from discord.ext import commands


class JakserahCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="jakserah", description="One last message from good ol' Jaks.")
    async def farewell(self, interaction):
        """A long and truly sorrowful goodbye message for the USN of SoT from Jakserah."""
        await interaction.response.defer(ephemeral=True)


        farewell_message = (
            "Heya {mention}, and thanks for running me. Today, January 20th 2025, "
            "I'm retiring from the USN. I've had a brilliant time in the server, sailing with a lot of great people, "
            "young and old, some of which who are still around, some long gone.\n\n"
            "So just a couple of thanks for the people who have meant a lot to me. First off <@623783877336629269>, who "
            "pulled me away from the spikey shores of the SoT Community discord and dragged me into the USN. "
            "<@238481535169331210>, for taking me in on the Maelstrom, and giving me a place to stay (and haven't left my "
            "entire career in the USN). For <@280045686798417921>, <@360301092468162571>, <@642701715224920085>, "
            "<@151394552547115008>, and <@244484830140563457>, who got me on my feet in the server, and helped me rise "
            "through the ranks.\n\n"
            "My Dutch friends <@380116958093377538>, <@399578765304266756>, <@761122159249850368>, and "
            "<@261573407135498241> whose faces I've never seen, but will probably recognise from a mile away if we ever "
            "were to cross paths (which is very likely in the Netherlands).\n\n"
            "For my fellow and much beloved geeks at NSC, <@646516242949341236>, <@281119159012556800>, and "
            "<@356631292500115456>, who suffered me endlessly whilst getting Paul on its feet.\n\n"
            "Can't forget <@968293580596736010> and <@809269506853306409>, the future of the Reliant and a freaking funny "
            "duo to have as SL's.\n\n"
            "One more time for <@557251813288574998>, <@215990848465141760>, and <@140988338432770058>, the honorable "
            "members of the BoA, for enduring my endless requests, ideas, and random banter.\n\n"
            "And lastly: there's a ton of people I'm not mentioning here that deserve it. But my roles are already removed "
            "so I gotta hurry. To all of you: Thanks for having me and thanks for all the good times!\n\n"
            "Cheers, Jakserah"
        )

        # Replace the placeholder with the command author's mention
        formatted_message = farewell_message.format(mention=interaction.user.mention)
        # Send the message
        await interaction.followup.send(content=formatted_message)

async def setup(bot: commands.Bot):
    await bot.add_cog(JakserahCog(bot))
