from random import randint, choice
import math

from discord.ext import commands
import discord

from Core.musiccore2 import (
    YTDLSource,
    Song,
    SongQueue,
    VoiceState,
    YTDLError,
    VoiceError,
)

# {0} = Song name {1} = Invoker nick {2} = random User in voice channel
# Feel free to add to this :)
RESPONSES = {
    "play": [
        "Do I have to?",
        "Really? {song}?",
        "Apparently {invoker} has bad taste.",
        "I wonder if {random} likes this song...",
    ],
    "skip": [
        "Impatient are we? Fine I'll skip.",
        "I didn't like that song anyway. SKIP!",
        "Aw, I liked {song}.",
        "Thank God, I hate {song}.",
        "{invoker} has bad taste.",
        "{invoker} has good taste.",
        "Gonna have to drink mouthwash after that one",
    ],
    "join": ["Woo, {random} is here too!", "Thanks for the invite {invoker}"],
}


def setup(client):
    client.add_cog(Music(client))


class Music(commands.Cog):
    def __init__(self, client: commands.bot):
        self.client = client
        self.voice_states = {}
        self.played = []  # See Issue

    def get_voice_state(self, ctx: commands.Context) -> VoiceState:
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = VoiceState(self.client, ctx)
            self.voice_states[ctx.guild.id] = state
        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.client.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context) -> bool:
        if not ctx.guild:
            raise commands.NoPrivateMessage(
                "This command can't be used in DM channels."
            )

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        await ctx.send("An error occurred: {}".format(str(error)))

    @commands.command(name="join", invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)

        else:
            ctx.voice_state.voice = await destination.connect()
        await ctx.send(
            choice(RESPONSES["join"]).format(
                invoker=ctx.author.nick, song=None, random=choice(destination.members)
            )
        )

    @commands.command(name="summon")
    async def _summon(
        self, ctx: commands.Context, *, channel: discord.VoiceChannel = None
    ):
        """Summons the client to a voice channel.
        If no channel was specified, it joins your channel.
        """

        if not channel and not ctx.author.voice:
            raise VoiceError(
                "You are neither connected to a voice channel nor specified a channel to join."
            )

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name="leave", aliases=["disconnect", "dc"])
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        if not ctx.voice_state.voice:
            return await ctx.send("I'm already out. What more do you want?")

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name="volume")
    async def _volume(self, ctx: commands.Context, *, volume: int):
        """Sets the volume of the player."""

        if not ctx.voice_state.is_playing:
            return await ctx.send(
                "The volume of _what_ exactly? I'm not playing anything."
            )

        if 0 > volume > 100:
            return await ctx.send("Volume must be between 0 and 100.")

        ctx.voice_state.volume = volume / 100
        await ctx.send("Volume of the player set to {}%".format(volume))

    @commands.command(name="now", aliases=["current", "playing"])
    async def _now(self, ctx: commands.Context):
        """Displays the currently playing song."""
        embed = ctx.voice_state.current.create_embed()
        await ctx.send(embed=embed)

    @commands.command(name="pause", aliases=["pa"])
    async def _pause(self, ctx: commands.Context):
        """Pauses the currently playing song."""
        print(">>>Pause Command:")
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction("⏯")

    @commands.command(name="resume", aliases=["re", "res"])
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song."""

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction("⏯")

    @commands.command(name="stop")
    async def _stop(self, ctx: commands.Context):
        """Stops playing song and clears the queue."""

        ctx.voice_state.songs.clear()

        if ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction("⏹")

    @commands.command(name="skip", aliases=["s"])
    async def _skip(self, ctx: commands.Context):
        """Vote to skip a song. The requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send("Not playing any music right now...")
        ctx.voice_state.skip()  # ctx.voice_state.current
        await ctx.send(
            choice(RESPONSES["skip"]).format(
                invoker=ctx.author.nick,
                song=ctx.voice_state.current,
                random=choice(ctx.author.voice.channel.members),
            )
        )

    @commands.command(name="queue")
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """Shows the player's queue.
        You can optionally specify the page to show. Each page contains 10 elements.
        """

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send("Empty queue.")

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ""
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += "`{0}.` [**{1.source.title}**]({1.source.url})\n".format(
                i + 1, song
            )

        embed = discord.Embed(
            description="**{} tracks:**\n\n{}".format(len(ctx.voice_state.songs), queue)
        ).set_footer(text="Viewing page {}/{}".format(page, pages))
        await ctx.send(embed=embed)

    @commands.command(name="shuffle")
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send("Empty queue.")

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction("✅")

    @commands.command(name="remove")
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a song from the queue at a given index."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send("Empty queue.")

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction("✅")

    @commands.command(name="loop")
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing song.
        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send("Yeah? What do you want me to loop? Silence?")

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction("✅")
        await ctx.send(
            "Looping a song is now turned " + ("on" if ctx.voice_state.loop else "off")
        )

    @commands.command(name="autoplay")
    async def _autoplay(self, ctx: commands.Context):
        """Automatically queue a new song that is related to the song at the end of the queue.
        Invoke this command again to toggle autoplay the song.
        """
        # TODO: FIX, error highlighted in issues
        if not ctx.voice_state.is_playing:
            return await ctx.send("Nothing being played at the moment.")

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.autoplay = not ctx.voice_state.autoplay
        await ctx.message.add_reaction("✅")
        await ctx.send(
            "Autoplay after end of queue is now "
            + ("on" if ctx.voice_state.autoplay else "off")
        )

    @commands.command(name="play", aliases=["p"])
    async def _play(self, ctx: commands.Context, *, search: str):
        """Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """
        # TODO: Add link support.
        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(
                    ctx, search, loop=self.client.loop
                )
            except YTDLError as e:
                await ctx.send(
                    "An error occurred while processing this request: {}".format(str(e))
                )
            else:
                if not ctx.voice_state.voice:
                    await ctx.invoke(self._join)

                song = Song(source)
                ctx.voice_state.previous.append(song)
                await ctx.voice_state.songs.put(song)
                await ctx.send(
                    choice(RESPONSES["play"]).format(
                        invoker=ctx.author.nick,
                        song=song,
                        random=choice(ctx.author.voice.channel.members),
                    )
                )
                await ctx.send("Enqueued {}".format(str(source)))

    @commands.command(name="search")
    async def _search(self, ctx: commands.Context, *, search: str):
        """Searches youtube.
        It returns an imbed of the first 10 results collected from youtube.
        Then the user can choose one of the titles by typing a number
        in chat or they can cancel by typing "cancel" in chat.
        Each title in the list can be clicked as a link.
        """
        # TODO: Make this a menu.
        async with ctx.typing():
            try:
                source = await YTDLSource.search_source(
                    ctx, search, loop=self.client.loop
                )
            except YTDLError as e:
                await ctx.send(
                    "An error occurred while processing this request: {}".format(str(e))
                )
            else:
                if source == "sel_invalid":
                    await ctx.send("Invalid selection")
                elif source == "cancel":
                    await ctx.send(":white_check_mark:")
                elif source == "timeout":
                    await ctx.send(":alarm_clock: **Time's up bud**")
                else:
                    if not ctx.voice_state.voice:
                        await ctx.invoke(self._join)

                    song = Song(source)
                    ctx.voice_state.previous.append(song)
                    await ctx.voice_state.songs.put(song)
                    if len(ctx.voice_state.songs) > 0:
                        await ctx.send("Enqueued {}".format(str(source)))

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError("You are not connected to any voice channel.")

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError("client is already in a voice channel.")
