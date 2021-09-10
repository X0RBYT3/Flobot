from datetime import datetime
import logging
import sys
import os
import colorlog

import discord
from discord.ext import commands

from Core.config import PREFIX, VERSION, OWNER_ID
log = logging.getLogger(__name__)
"""
The main Client file.
bot 'globals' go into Client.__init__() if they need to be used across commands.

TODO: Add on_ready runs when the bot is loaded, but not yet on discord. Will need to be changed if bot goes public.

"""
INTRO = "==========================\nFlobot - V:{0}\n==========================\n".format(
    VERSION
)
AUDIO_CACHE = os.path.join(os.getcwd(), 'audio_cache')

class MyHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(color=discord.Color.blurple(), description='')
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)

def check(ctx):
    if ctx.bot.locked and not ctx.author.guild_permissions.manage_messages:
        return False
    return True


class Client(commands.Bot):
    def __init__(self, cogs):

        super().__init__(
            command_prefix=PREFIX, case_insensitive=True
        )
        self.help_command = MyHelpCommand()
        self.owner_id = OWNER_ID  # Flo
        self.uptime = datetime.now()
        self._version = VERSION
        self.debug_level = 'INFO'
        self._setup_logging()

        self.locked = False  # Implementing Locking functionality
        self.add_check(check)
        for cog in cogs:
            try:
                self.load_extension("Cogs." + cog)
            except Exception as e:
                exc = "{}: {}".format(type(e).__name__, e)
                log.warning(
                    "Cog Loading Failed: {0}\n{1}".format(
                        cog, exc))
            else:
                log.info("Cog Loading Successful: {0}".format(cog))
        log.info(
            "{0} Out of {1} Cogs Loaded".format(len(self.cogs), len(cogs))
        )
    def _setup_logging(self):
        if len(logging.getLogger(__package__).handlers) > 1:
            log.debug("Logger already setup, skipping setup.")
        shandler = logging.StreamHandler(stream=sys.stdout)
        shandler.setFormatter(colorlog.LevelFormatter(
            #
            fmt={
                'DEBUG': '{log_color}[{levelname}:{module}] {message}',
                'INFO': '{log_color}{message}',
                'WARNING': '{log_color}{levelname}: {message}',
                'ERROR': '{log_color}[{levelname}:{module}] {message}',
                'CRITICAL': '{log_color}[{levelname}:{module}] {message}',

                'EVERYTHING': '{log_color}[{levelname}:{module}] {message}',
                'NOISY': '{log_color}[{levelname}:{module}] {message}',
                'VOICEDEBUG': '{log_color}[{levelname}:{module}][{relativeCreated:.9f}] {message}',
                'FFMPEG': '{log_color}[{levelname}:{module}][{relativeCreated:.9f}] {message}'
            },
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'white',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',

                'EVERYTHING': 'white',
                'NOISY': 'white',
                'FFMPEG': 'bold_purple',
                'VOICEDEBUG': 'purple',
            },
            style='{',
            datefmt=''
        ))
        shandler.setLevel(self.debug_level)
        logging.getLogger(__package__).addHandler(shandler)

        log.debug("Set logging level to {}".format(self.debug_level))

        dlogger = logging.getLogger('discord')
        dlogger.setLevel(logging.DEBUG)
        dhandler = logging.FileHandler(filename='logs/discord.log', encoding='utf-8', mode='w')
        dhandler.setFormatter(logging.Formatter('{asctime}:{levelname}:{name}: {message}', style='{'))
        dlogger.addHandler(dhandler)
