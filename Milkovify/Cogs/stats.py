import datetime
import time
import platform

import discord
from discord.ext import commands

from Core.config import logger, github
from Core import checks
from Core.Utils.chat_formatter import humanize_timedelta


def setup(client):
    client.add_cog(Stats(client))


class Stats(commands.Cog):
    """
    Provides some neat stats on the Bot.

    PING: Measures ping
    UPTIME: Measures uptime
    ABOUT: Gives nice data on memory usage and the such

    todo: add github.

    """

    def __init__(self, client):
        self.client = client

    @commands.command(name="ping", usage=";ping")
    async def ping(self, ctx):
        """
        Measures how long until a message is sent to Discord and detected.
        """
        ping = ctx.message
        pong = await ctx.send("**:ping_pong:** Pong!")
        delta = pong.created_at - ping.created_at
        delta = int(delta.total_seconds() * 1000)
        await pong.edit(
            content=f":ping_pong: Pong! ({delta} ms)\n*Discord WebSocket Latency: {round(self.client.latency, 5)} ms*"
        )
        return

    def get_client_uptime(self, brief=False):
        """
        works well enough for what it does
        have a feeling it could be better
        """
        now = datetime.datetime.now()
        delta = now - self.client.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        if brief:
            fmt = "{h}h {m}m {s}s"
            if days:
                fmt = "{d}d " + fmt
            return fmt.format(d=days, h=hours, m=minutes, s=seconds)
        return humanize_timedelta(delta)

    @commands.command(name="uptime", usage=";uptime")
    # @commands.check(checks.is_mod_or_superior)
    async def uptime(self, ctx):
        """
        Gets the time since the bot first connected to Discord
        """
        now = datetime.datetime.now()
        delta = now - self.client.uptime

        em = discord.Embed(
            title="Local time",
            description=str(datetime.datetime.now())[:-7],
            colour=0x14E818,
        )
        em.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
        em.add_field(
            name="Current uptime", value=self.get_client_uptime(brief=True), inline=True
        )
        em.add_field(name="Start time", value=str(self.client.uptime)[:-7], inline=True)
        em.set_footer(
            text="Made with 💖 by Florence",
            icon_url="https://media.giphy.com/media/qjPD3Me0OCvFC/giphy.gif",
        )
        await ctx.send(embed=em)

    @commands.command(name="about", usage=";about")
    # @commands.check(checks.is_mod_or_superior)
    async def about(self, ctx):
        embed = discord.Embed(description="ABOUT ME, THE BOT")
        embed.title = "About:"
        embed.colour = 0x738BD7

        owner = self.client.get_user(self.client.owner_id)
        if owner is not None:
            embed.set_author(name=str(owner), icon_url=owner.avatar_url)

        total_members = sum(1 for _ in self.client.get_all_members())
        total_online = len(
            {
                m.id
                for m in self.client.get_all_members()
                if m.status is discord.Status.online
            }
        )
        total_unique = len(self.client.users)

        voice_channels = []
        text_channels = []
        for guild in self.client.guilds:
            voice_channels.extend(guild.voice_channels)
            text_channels.extend(guild.text_channels)

        embed.add_field(
            name="Members",
            value=f"{total_members} total\n{total_unique} unique\n{total_online} unique online",
        )
        # embed.add_field(
        # name='Channels', value=f'{text + voice} total\n{text} text\n{voice} voice')
        embed.add_field(name="Guilds", value=len(self.client.guilds))
        embed.add_field(name="Version", value=self.client._version)
        embed.add_field(
            name="Python Version", value=platform.python_version(), inline=True
        )
        embed.add_field(name="Uptime", value=self.get_client_uptime(brief=True))
        embed.set_footer(
            text="Made with 💖 by Florence",
            icon_url="https://media.giphy.com/media/qjPD3Me0OCvFC/giphy.gif",
        )
        await ctx.send(embed=embed)
