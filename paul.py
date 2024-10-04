#Paul Bot Made for USNofSOT

#Imports
import discord
from discord import Intents, Client, Message
from typing import Final
import os
from dotenv import load_dotenv
from database_manager_mysql import DatabaseManager


#Load token

load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

#bot setup
intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)

# startup

@client.event
async def on_ready() -> None:
	print(f'{client.user} is now running!')

#initiate db manager and commands class

db_manager = DatabaseManager()

# / Command Calls

# ! Command Calls



# Main Entry point
def main() -> None:
	client.run(token=TOKEN)

if __name__ == '__main__':
	main()