from src.config.main_server import VOYAGE_LOGS
from src.utils.embeds import error_embed

async def get_recent_user_log_id(bot, user_id):
    # get the voyage logs channel, if none found then stop
    logs_channel = bot.get_channel(VOYAGE_LOGS)
    if logs_channel is None:
        return None

    # loops to find the most recent log by the command user, skips any done by anyone else
    async for message in logs_channel.history(limit=25):
        if message.author.id == user_id:
            return str(message.id)

    # if no matching message is found then return none
    return None



async def resolve_log_id(bot, interaction, log_id):
    # if no input is provided, check for log from user in voyage log channel
    if log_id is None:
        log_id = await get_recent_user_log_id(bot, interaction.user.id)

        if log_id is None:
            await interaction.followup.send(
                embed=error_embed(
                    description="No recent voyage log by you found in last 25 logs. Please provide a log ID."
                ),
                ephemeral=True,
            )
            return None

    else:
        original_input = log_id
        log_id = log_id.strip()

        # Discord message link
        if "discord.com/channels/" in log_id or "discordapp.com/channels/" in log_id:
            log_id = log_id.split("/")[-1].split("?")[0]

        if not log_id.isdigit():
            await interaction.followup.send(
                embed=error_embed(
                    description="Invalid Discord message ID. Please provide a valid message ID."
                ),
                ephemeral=True,
            )
            return None

    return log_id
