from discord.ext import commands
import discord

from Core import permissions


def mod_check(ctx) -> bool:
    """
    We can assume anyone with manage_messages is a mod.

    This should be a decorator.
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


def setup(client):
    client.add_cog(OwnerCog(client))
