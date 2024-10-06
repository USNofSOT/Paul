# Paul
USNofSOTBot


Libraries in use:
DateTime        5.5
discord         2.3.2
discord.py      2.4.0
mariadb         1.1.10
python-env      1.0.0
python-dotenv   1.0.1
load-dotenv     0.1.0


Structure of the bot is as follows:

paul.py is the main code of the bot, all areas should be commented in:
""" Imports - 0 """ - brings in libraries as needed
""" Bot Setup - 1""" - Token import, bot definition, database_manger initializer, On.ready commands
""" Passive Handlers - 2 """ - These happen passively as events happen on the server
""" Slash Commands - 3 """ - are the commands that use "/" to load and have and interface, the main parts of the bot
""" Commands - 4 """ - commands based on the ! - these are unlisted and used for functions that are reserved.
""" Utilities - 5 """ - background functions, and commands not part of the core of the bot (i.e. ping)

