from datetime import datetime

import discord
from discord.ext import commands

from Core.config import logger, PREFIX, DESCRIPTION, AUTHOR, VERSION

"""
The main Client file.
bot 'global' variables go in the __init__ if they need to be used across commands.

on_ready runs when the bot is loaded, but not yet on discord. Will need to be changed if bot goes public.

"""
INTRO = "==========================\nMILKOVIFY - V:{0}\n==========================\n".format(
    VERSION
)


def check(ctx):
    if ctx.bot.locked and not ctx.author.guild_permissions.manage_messages:
        return False
    return True


class Client(commands.Bot):
    def __init__(self, cogs):

        super().__init__(
            command_prefix=PREFIX, case_insensitive=True, description=DESCRIPTION
        )
        self.owner_id = 24239825185524942  # Flo
        self.uptime = datetime.now()
        self._version = VERSION

        self.logger = logger
        self.logger.set_level("GENERAL")

        self.locked = False  # Implementing Locking functionality
        self.add_check(check)
        for cog in cogs:
            try:
                self.load_extension("Cogs." + cog)
            except Exception as e:
                exc = "{}: {}".format(type(e).__name__, e)
                self.logger.CRITICAL("Cog Loading Failed: {0}\n{1}".format(cog, exc))
            else:
                self.logger.GENERAL("Cog Loading Successful: {0}".format(cog))
        self.logger.GENERAL(
            "{0} Out of {1} Cogs Loaded".format(len(self.cogs), len(cogs))
        )
