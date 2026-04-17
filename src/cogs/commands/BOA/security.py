import discord
from discord import app_commands
from discord.ext import commands

from src.security import require_any_role, Role
from src.security.repository import SecurityInteractionRepository
from src.utils.embeds import default_embed


class SecurityManagement(commands.Cog):
    """
    Cog for security-related management commands, restricted to BOA and Administrators.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="security_logs", description="View recent security interaction logs")
    @require_any_role(Role.BOA, Role.NSC_ADMINISTRATOR)
    @app_commands.describe(limit="Number of logs to show (max 25)")
    async def security_logs(self, interaction: discord.Interaction, limit: int = 10):
        """
        Displays the most recent security interaction logs in an embed.
        """
        limit = max(1, min(limit, 25))

        try:
            with SecurityInteractionRepository() as repo:
                logs = repo.get_recent_logs(limit)
        except Exception as e:
            await interaction.response.send_message(f"Error fetching logs: {e}", ephemeral=True)
            return

        if not logs:
            await interaction.response.send_message("No security logs found.", ephemeral=True)
            return

        embed = default_embed(title="Recent Security Interaction Logs")

        for log_entry in logs:
            # Format user name
            user = self.bot.get_user(log_entry.discord_id)
            user_name = user.mention if user else f"Unknown ({log_entry.discord_id})"

            # Format timestamp
            timestamp = log_entry.created_at.strftime('%Y-%m-%d %H:%M:%S')

            # Color indicator based on event type
            status_emoji = "✅" if log_entry.event_type.name == "SUCCESS" else "❌"

            field_name = f"{status_emoji} {timestamp} - {log_entry.event_type.name}"
            field_value = (
                f"**User:** {user_name}\n"
                f"**Command:** `{log_entry.command_name}`\n"
                f"**Details:** {log_entry.details or 'None'}"
            )

            # Add arguments if present and not too long
            if log_entry.args and log_entry.args != "{}":
                args_str = log_entry.args
                if len(args_str) > 100:
                    args_str = args_str[:97] + "..."
                field_value += f"\n**Args:** `{args_str}`"

            embed.add_field(name=field_name, value=field_value, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SecurityManagement(bot))
