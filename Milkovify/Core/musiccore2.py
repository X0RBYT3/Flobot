import asyncio
import functools
import itertools


import discord
from discord.ext import commands
import youtube_dl
from async_timeout import timeout
import httpx
from bs4 import BeautifulSoup
import random

# Silence, nerd.
youtube_dl.utils.bug_reports_message = lambda: ""


class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        "format": "bestaudio/best",
        "extractaudio": True,
        "audioformat": "mp3",
        "outtmpl": "song-%(extractor)s-%(id)s-%(title)s.%(ext)s",
        "restrictfilenames": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "default_search": "auto",
        "source_address": "0.0.0.0",
    }
    FFMPEG_OPTIONS = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn",
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)
    ytdl.cache.remove()

    def __init__(
        self,
        ctx: commands.Context,
        source: discord.FFmpegPCMAudio,
        *,
        data: dict,
        volume: float = 0.5,
    ):

        super().__init__(source, volume)

        ## Get us some of that sweet sweet info
        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get("uploader")
        self.uploader_url = data.get("uploader_url")
        date = data.get("upload_date")
        self.upload_date = date[6:8] + "." + date[4:6] + "." + date[0:4]
        self.title = data.get("title")
        self.thumbnail = data.get("thumbnail")
        self.description = data.get("description")
        self.duration = self.parse_duration(int(data.get("duration")))
        self.tags = data.get("tags")
        self.url = data.get("webpage_url")
        self.views = data.get("view_count")
        self.likes = data.get("like_count")
        self.dislikes = data.get("dislike_count")
        self.stream_url = data.get("url")

    def __str__(self):
        """
        Used for !playing and Status.
        Note due to status, this cannot be formatted via discord formatting
        eg: **, __, ```, etc.
        """
        return "{0.title} by {0.uploader}".format(self)

    @classmethod
    async def create_source(
        cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None
    ):

        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(
            cls.ytdl.extract_info, search, download=False, process=False
        )
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError("Could not find anything that matches {0}.".format(search))

        if "entries" not in data:
            process_info = data
        else:
            process_info = None
            for entry in data["entries"]:
                if entry:
                    process_info = entry
                    break
            if process_info is None:
                raise YTDLError(
                    "Could not find anything that matches {0}.".format(search)
                )
        webpage_url = process_info["webpage_url"]
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError("Could not fetch {0}".format(webpage_url))

        if "entries" not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info["entries"].pop(0)
                except IndexError:
                    raise YTDLError(
                        "Couldn't retrieve any matches for `{}`".format(webpage_url)
                    )

        return cls(
            ctx, discord.FFmpegPCMAudio(info["url"], **cls.FFMPEG_OPTIONS), data=info
        )

    @staticmethod
    def parse_duration(duration: int):
        """
        Jank af.
        """
        if duration > 0:
            minutes, seconds = divmod(duration, 60)
            hours, minutes = divmod(minutes, 60)
            days, hours = divmod(hours, 24)

            duration = []
            if days > 0:
                duration.append("{} days".format(days))
            if hours > 0:
                duration.append("{} hours".format(hours))
            if minutes > 0:
                duration.append("{} minutes".format(minutes))
            if seconds > 0:
                duration.append("{} seconds".format(seconds))
            value = ":".join(duration)

        elif duration == 0:
            value = "LIVE"

        return value


class Song:
    __slots__ = ("source", "requester")

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (
            discord.Embed(
                title="Now playing",
                description="```css\n{0.source.title}\n```".format(self),
                color=discord.Color.blurple(),
            )
            .add_field(name="Duration", value=self.source.duration)
            .add_field(name="Requested by", value=self.requester.mention)
            .add_field(
                name="Uploader",
                value="[{0.source.uploader}]({0.source.uploader_url})".format(self),
            )
            .add_field(name="URL", value="[Click]({0.source.url})".format(self))
            .set_thumbnail(url=self.source.thumbnail)
        )

        return embed

    def __str__(self):
        return self.source.title


class SongQueue(asyncio.Queue):
    """
    This is jank af
    """

    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        """
        Throughout the rest of this project I'm using client
        so I'm using it here
        fuck you
        """
        self.client = bot
        self._ctx = ctx

        self.exists = True
        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self.previous = []

        self._loop = False
        self._volume = 0.5
        self.audio_player = bot.loop.create_task(self.audio_player_task())

        self._timeout = 240
        self._autoplay = False

    def __def__(self):
        self.audio_player.cancel()

    @property
    def loop(self) -> bool:
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def timeout(self) -> int:
        return self._timeout

    @timeout.setter
    def timeout(self, value: int):
        self._timeout = value

    @property
    def autoplay(self):
        return self._autoplay

    @autoplay.setter
    def autoplay(self, value: bool):
        self._autoplay = value

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        """
        This is a big function, so will require some explaining

        This func can be boiled down to the psuedocode

        if autoplay enabled:
            wait 3 seconds for new song
            if no new songs:
                grab a new song off youtube
                play it
            if new song:
                play it

        else:
            wait 5 minutes for a new song
            if no new songs:
                disconnect
            if new song:
                play it
        """
        while True:
            self.next.clear()
            if self.autoplay:
                try:
                    async with timeout(3):
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    # Spoof user agent to show whole page.
                    headers = {
                        "User-Agent": "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)"
                    }
                    song_url = self.current.source.url
                    # Get the page
                    async with httpx.AsyncClient() as client:
                        response = await client.get(song_url, headers=headers)

                    soup = BeautifulSoup(response.text, features="lxml")

                    # Parse all the recommended videos out of the response and store them in a list
                    recommended_urls = []
                    for li in soup.find_all("li", class_="related-list-item"):
                        a = li.find("a")

                        # Only videos (no mixes or playlists)
                        if "content-link" in a.attrs["class"]:
                            recommended_urls.append(
                                f'https://www.youtube.com{a.get("href")}'
                            )

                    ctx = self._ctx

                    async with ctx.typing():
                        try:
                            print(recommended_urls)
                            source = await YTDLSource.create_source(
                                ctx, recommended_urls[0], loop=self.bot.loop
                            )
                        except YTDLError as e:
                            await ctx.send(
                                "An error occurred while processing this request: {}".format(
                                    str(e)
                                )
                            )
                            self.bot.loop.create_task(self.stop())
                            self.exists = False
                            return
                        else:
                            song = Song(source)
                            self.played.append(song)
                            self.current = song
                            await ctx.send("Enqueued {}".format(str(source)))

            else:
                if not self.loop:
                    # Try to get the next song within 5 minutes.
                    # If no song will be added to the queue in time,
                    # the player will disconnect due to performance
                    # reasons.
                    try:
                        async with timeout(self._timeout):  # 5 minutes
                            self.current = await self.songs.get()
                    except asyncio.TimeoutError:
                        self.bot.loop.create_task(self.stop())
                        return
            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(embed=self.current.create_embed())

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None
