# Paul
This repository contains the source code for the Discord bot named Paul, used by [The United Stated Navy of Sea of Thieves](https://discord.gg/343XSEha). The bot manages sailor records for the server which includes:

- Voyage participation and hosting
- Medals and awards
- Disciplinary notes

:heavy_exclamation_mark: **Status** :heavy_exclamation_mark:

The bot is currently under active (re)development by Navy Systems Command.
It is not yet ready for widespread use.

The developer and users guides will eventually find themselves in GitHub pages.
This site will only be accessible to developers with access to the repo.
Users guides for various groups could be auto-generated PDFs, with links put in appropriate embeds (e.g. nrc-info).


## Developer Guide

### Initial Setup
- Clone this repo
- Open the repo in Visual Studio Code
- Create a virtual environment for the repo using Python 3.12 and the requirements listed in [requirements.txt](https://github.com/USNofSOT/Paul/blob/main/requirements.txt).
- Copy the file content from [Navy Systems Command > engine-room](https://discord.com/channels/971718695602778162/1288304233409548309/1293910688900714518) into a file named `.env` at the top level of the repo
- Include `PYTHONPATH=./src;${PYTHONPATH}` at the top of the `.env` file


### GitHub Workflow
Changes to the main branch can only be made by approved pull requests. Regardless of the size of the change or the author, everything is tracked through pull requests with approval.

To make a change, create a new branch from main. You can do this by running `>Git: Create Branch...` from the search bar at the top of the window in Visual Studio Code. To commit your code changes to the branch, you can first click the Source Control icon in the left sidebar then select the plus sign next to the files you changed. Next write a brief summary of the changes in the Message box, then finally click Commit. When you are ready to push the commit(s) to GitHub, click the three dots menu next to Source Control then choose Pull, Push > Push.

Developers familiar with using git from the command line can `add`, `commit`, `push`, etc from a command window if they prefer.


### Linking PAUL_TESTING to your local repo
You can link the PAUL_TESTING bot to your local copy of the repo. To do this,
first confirm in the [Navy Systems Command > engine-room](https://discord.com/channels/971718695602778162/1288304233409548309) channel that no one else is using it. If so, navigate to `main.py` and click the run arrow in the top right of the window. If successful, there will be some code printed to the screen such as

```
2024-10-13 16:23:56 INFO     utils.process_voyage_log [1295140713666707496] Processing voyage log for host: 209018181916950531 with 3 participants.
```

Now you can run commands in the [BOT TESTING > bot-test-command](https://discord.com/channels/933907909954371654/1291589569602650154) channel with PAUL_TESTING.


### Repository Setup
Updated Bot setup:

- `src` holds the full Bot.
- `src/main.py` starts the bot which is located in the core\bot.py file.
- `src/cogs` folder holds the individual command files the bot runs from.
- `src/data` folder holds the database utilites.
- `src/utils` folder holds utility classes that are imported to the cog based commands as needed.


## Users Guide
:heavy_exclamation_mark: **Work in Progress** :heavy_exclamation_mark:

The following sections provide brief descriptions for each of the bot commands. Further details may be added later, and linked where appropriate.


### All Users
All members of the server have access to the following commands:

- `/member` Run a member report on yourself or others.
- `/ping` Ping the bot to verify it is running.
- `/setinfo` Update your gamertag and/or timezone.


### Voyage Hosts
Voyage hosts have access to the following commands:

- `/addsubclass` Give subclass points to your crew from an official voyage.

### Officers
Officers (O-1+) have access to the following commands:

- `/addcoin` Give your challenge coin to someone.


### Navy Recruit Command
Members of the Navy Recruiting Command (NRC) have access to the following commands:

- `/addinfo` Add the gamertag and timezone for a recruit.
