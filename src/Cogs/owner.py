import asyncio
import logging

from discord.ext import commands
import discord

from Core import permissions

log = logging.getLogger(__name__)
def mod_check(ctx) -> bool:
    """
    We can assume anyone with manage_messages is a mod.

    This should be a decorator, but I'm lazy right now.
    """
    if ctx.author.guild_permissions.manage_messages:
        return True
    return False


class OwnerCog(commands.Cog):
    """
    haha 'owner'.

    """

    def __init__(self, client):
        self.client = client
        self.last_cog = ""

    @commands.command(name="echo", aliases=["say"])
    async def say(self, ctx, channel: discord.TextChannel, *, message_to_say):
        if not mod_check(ctx):
            return
        await channel.send(message_to_say)

    @commands.command()
    async def shutdown(self, ctx):
        """
        Emergency usage only.
        """
        if not mod_check(ctx):
            return
        await ctx.send("Shutting down, I love you.")
        await self.client.close()

    @commands.command()
    async def load(self, ctx, *, cog: str):
        """Command which loads a Module.
        Remember to use dot path. e.g: cogs.owner"""
        if not mod_check(ctx):
            return
        try:
            self.client.load_extension("Cogs." + cog)
        except Exception as e:
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
        else:
            await ctx.send("**`SUCCESS`**\N{PISTOL}")
        self.last_cog = cog

    @commands.command()
    async def unload(self, ctx, *, cog: str):
        """Command which Unloads a Module.
        Remember to use dot path. e.g: cogs.owner"""
        if not mod_check(ctx):
            return
        try:
            self.client.unload_extension("Cogs." + cog)
        except Exception as e:
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
        else:
            await ctx.send("**`SUCCESS`**\N{PISTOL}")
            self.last_cog = cog

    @commands.command(name="reload")
    async def rel(self, ctx, *, cog: str):
        """Command which Reloads a Module.
        Remember to use dot path. e.g: cogs.owner"""
        if not mod_check(ctx):
            return
        try:
            if cog.lower() == "last":
                if self.last_cog != "":
                    cog = self.last_cog
                else:
                    await ctx.send(f"**`ERROR:`** No Last Cog")
            self.client.unload_extension("Cogs." + cog)
            self.client.load_extension("Cogs." + cog)
        except Exception as e:
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
        else:
            await ctx.send("**`SUCCESS`**\N{PISTOL}")
        self.last_cog = cog

    @commands.command(name="lock")
    async def lock(self, ctx):
        if not mod_check(ctx):
            return
        self.client.locked = not self.client.locked
        await ctx.send("Set the lock to: **{0}**".format(self.client.locked))

    @commands.command()
    async def status(self, ctx: commands.Context, *args):
        def check(m):
            return m.channel == ctx.channel and m.author.id == 826933707994169365 and 'successfully' in m.content

        try:
            _ = await ctx.bot.wait_for('message', check=check, timeout=2)
            # LazyBot responded with success, the command input must be valid then
            userid = int(args[0])
            form = args[1].split('/')
            if form[0].lower() != 'belts':
                # Seems like this is some other type of form we don't support yet
                # Let's just ignore it.
                return
            status = args[2].lower().startswith('accept')

            belt_channel = ctx.bot.get_channel(827740601054265344)
            # Loop through the latest 10 submissions until we find one that matches
            # the command
            async for submission in belt_channel.history(limit=10):
                embed = submission.embeds[0]
                if embed.title.lower().split(' ')[0] == form[1].lower() and str(userid) in embed.description:
                    if status:
                        return await submission.add_reaction('✅')
                    else:
                        return await submission.add_reaction('❌')

            # We couldn't find the submission. Oh well.
        except asyncio.TimeoutError:
            # LazyBot either didn't respond, or didn't like the command, so we likely shouldn't either
            return


def setup(client):
    client.add_cog(OwnerCog(client))
