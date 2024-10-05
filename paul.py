#Paul Bot Made for USNofSOT

#Imports

import datetime
import discord
import os

from database_manager import DatabaseManager
from datetime import datetime, timezone
from discord import Intents, Client, Message
from discord.ext.commands import Bot
from dotenv import load_dotenv
from typing import Final


#Load token

load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

#bot setup
intents: Intents = Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True

current_time = datetime.now(timezone.utc)

bot = Bot(command_prefix=['/', '!'], intents=intents)

# startup

@bot.event
async def on_ready() -> None:
	print(f'{bot.user} is now running!')

#initiate db manager and commands class

db_manager = DatabaseManager()

# / Command Calls

# ! Command Calls



# Main Entry point
def main() -> None:
	bot.run(token=TOKEN)

if __name__ == '__main__':
	main()