from datetime import datetime
import math
import decimal
import logging

from discord.ext import commands, tasks
import discord

log = logging.getLogger(__name__)
dec = decimal.Decimal


def setup(client):
    client.add_cog(RandomStuff(client))


class RandomStuff(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.roosters = None
        self.rooster_id = 855148879891922985
        self.change_rooster.start()

    def position(self, now=None):
        if now is None:
            now = datetime.now()
        diff = now - datetime(2001, 1, 1)
        days = dec(diff.days) + (dec(diff.seconds) / dec(86400))
        lunations = dec("0.20439731") + (days * dec("0.03386319269"))

        return lunations % dec(1)

    def phase(self, pos):
        index = (pos * dec(8)) + dec("0.5")
        index = math.floor(index)
        return {
            0: ["New Moon", " 🌑 "],
            1: ["Waxing Crescent", " 🌒 "],
            2: ["First Quarter", " 🌓 "],
            3: ["Waxing Gibbous", " 🌔 "],
            4: ["Full Moon", " 🌕 "],
            5: ["Waning Gibbous", " 🌖 "],
            6: ["Last Quarter", " 🌗 "],
            7: ["Waning Crescent", " 🌘 "],
        }[int(index) & 7]

    @tasks.loop(hours=24)
    async def change_rooster(self):
        """
        Checks the first character of the channel (emoji)
        against the emoji of the current moon phase.

        Runs every 24 hours (first run is when bot is run.)
        """
        if self.roosters is None:
            self.roosters = await self.client.fetch_channel(self.rooster_id)
        pos = self.position()
        phasename = self.phase(pos)
        if phasename[1].strip() != self.roosters.name[0].strip():
            ## We got a new phase boys
            newname = phasename[1].strip() + self.roosters.name[1:]
            await self.roosters.send(
                "We move into a new phase {1}.\n Commencing {0}.".format(
                    phasename[0], phasename[1]
                )
            )
            log.info('Changed phase')
            await self.roosters.edit(name=newname)
