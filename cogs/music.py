import discord
from discord.ext import commands
import random
from yt_dlp import YoutubeDL
import asyncio

class YTDLSource(discord.AudioSource):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'auto',
        'quiet': True,
        'live_from_start': True,
        'nocheckcertificate': True,
        'source_address': '0.0.0.0',  # Bind to IPv4 since IPv6 might cause issues
    }
    FFMPEG_OPTIONS_BASE = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 '
                          '-probesize 32K -analyzeduration 0',
        'options': '',
    }

    FILTERS = {
        'normal': '',
        'nightcore': 'asetrate=44100*1.25,aresample=44100',
        'slowed': 'asetrate=44100*0.85,aresample=44100',
    }

    def __init__(self, source, *, data, mode='normal'):
        self.source = source  # This is the FFmpegOpusAudio source
        self.data = data
        self.mode = mode
        self.title = data.get('title')
        self.url = data.get('webpage_url')
        self.thumbnail = data.get('thumbnail')
        self.requester = data.get('requester')

    @classmethod
    async def create_source(cls, ctx, search, *, loop, mode='normal'):
        loop = loop or asyncio.get_event_loop()
        ytdl = YoutubeDL(cls.YTDL_OPTIONS)

        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(search, download=False)
        )

        if 'entries' in data:
            data = data['entries'][0]

        # Adjust FFmpeg options based on mode
        filter_option = cls.FILTERS.get(mode, '')
        before_options = cls.FFMPEG_OPTIONS_BASE['before_options']
        if filter_option:
            options = f'-vn -af "{filter_option}"'
        else:
            options = '-vn'

        # Use FFmpegOpusAudio
        source = discord.FFmpegOpusAudio(
            data['url'],
            before_options=before_options,
            options=options
        )

        return cls(source, data=data, mode=mode)

    def read(self):
        return self.source.read()

    def is_opus(self):
        return True  # Indicate that this source is already Opus-encoded

    def cleanup(self):
        self.source.cleanup()

class MusicPlayer:
    def __init__(self, ctx):
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        self.current = None
        self.volume = 1
        self.voice_client = ctx.voice_client
        self.is_streaming = None  # Indicates if a stream is active

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        while True:
            self.next.clear()
            try:
                # Regular mode: play songs from the queue
                try:
                    self.current = await self.queue.get()
                except asyncio.TimeoutError:
                    # No songs added for a while; disconnect
                    embed = discord.Embed(
                        title=random.choice(["Party's Over!", "Silence...", "Empty Stage!"]),
                        description="No songs have been added for a while. Leaving the voice channel.",
                        color=discord.Color.red()
                    )
                    await self.channel.send(embed=embed)
                    await self.cleanup()
                    return

                # Play the current source
                self.guild.voice_client.play(
                    self.current,
                    after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set)
                )

                # Now Playing Embed
                embed = discord.Embed(
                    title=f"Now Playing ({self.current.mode.capitalize()} Mode)",
                    description=f"[{self.current.title}]({self.current.url})",
                    color=discord.Color.blue(),
                )
                embed.set_thumbnail(url=self.current.thumbnail)
                embed.set_author(
                    name=f"Requested by {self.current.requester}",
                    icon_url=getattr(self.current.requester.avatar, 'url', None)
                )
                await self.channel.send(embed=embed)

                await self.next.wait()

                # Check if the queue is empty after the song finishes
                if self.queue.empty():
                    embed = discord.Embed(
                        title=random.choice(["All Done!", "That's All Folks!", "No More Songs!"]),
                        description="Playback finished. Leaving the voice channel.",
                        color=discord.Color.green()
                    )
                    await self.channel.send(embed=embed)
                    await self.cleanup()
                    return
            except Exception as e:
                # Log the exception
                print(f"Error in player_loop: {e}")
                await asyncio.sleep(1)  # Prevent tight loop in case of errors
                continue  # Proceed to the next iteration

    async def cleanup(self):
        """Helper function to disconnect and clean up resources."""
        self.current = None
        self.queue = asyncio.Queue()

        if self.guild.voice_client:
            await self.guild.voice_client.disconnect()

        # Remove the player instance from the bot's cache
        try:
            del self.bot.get_cog("Music").players[self.guild.id]
        except KeyError:
            pass

    def skip(self):
        self.guild.voice_client.stop()

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    def get_player(self, ctx):
        player = self.players.get(ctx.guild.id)
        if not player:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player
        return player

    @commands.command()
    async def play(self, ctx, *, search: str):
        await self._play(ctx, search, mode='normal')

    @commands.command(name='nightcore')
    async def play_nightcore(self, ctx, *, search: str):
        """Play a song in nightcore mode."""
        await self._play(ctx, search, mode='nightcore')

    @commands.command(name='slowed')
    async def play_slowed(self, ctx, *, search: str):
        """Play a song in slowed mode."""
        await self._play(ctx, search, mode='slowed')

    async def _play(self, ctx, search: str, *, mode: str):
        player = self.get_player(ctx)

        if ctx.author.voice is None:
            await ctx.send("You need to join a voice channel first.")
            return

        voice_channel = ctx.author.voice.channel

        # Ensure the bot is connected to the voice channel
        if ctx.voice_client is None:
            await voice_channel.connect()
        elif ctx.voice_client.channel != voice_channel:
            await ctx.voice_client.move_to(voice_channel)

        source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, mode=mode)
        source.requester = ctx.author

        await player.queue.put(source)

        # Added to Queue Embed
        embed = discord.Embed(
            title="Added to Queue",
            description=f"[{source.title}]({source.url})",
            color=discord.Color.green(),
        )
        embed.set_thumbnail(url=source.thumbnail)
        embed.set_footer(
            text=f"Mode: {mode.capitalize()} | Position in queue: {player.queue.qsize()}"
        )

        await ctx.send(embed=embed)

    @commands.command(name='skip')
    async def skip_(self, ctx):
        """Skip the current song."""
        player = self.get_player(ctx)

        if ctx.voice_client is None or not ctx.voice_client.is_playing():
            embed = discord.Embed(
                title=random.choice(["No Music!", "Oops!", "Can't Skip Nothing!"]),
                description="Nothing is playing.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        player.skip()

        embed = discord.Embed(
            title=random.choice(["Skipped!", "Next Up!", "Song Skipped!"]),
            description="Skipped the current song.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='stop')
    async def stop_(self, ctx):
        """Stop the player and clear the queue."""
        player = self.get_player(ctx)

        if player.is_streaming:
            embed = discord.Embed(
                title="Cannot Stop Stream",
                description="Use `stopstream` to stop the ongoing stream.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if ctx.voice_client is None:
            embed = discord.Embed(
                title=random.choice(["Not Connected!", "Hmm...", "No Music Found!"]),
                description="Not connected to a voice channel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        player.queue = asyncio.Queue()  # Clear the queue
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()

        embed = discord.Embed(
            title=random.choice(["Stopped!", "Music Halted!", "Goodbye Music!"]),
            description="Player stopped and queue cleared.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @commands.command(name='queue', aliases=['q'])
    async def queue_info(self, ctx):
        """Display the current queue."""
        player = self.get_player(ctx)

        if player.is_streaming:
            embed = discord.Embed(
                title="Currently Streaming",
                description="A stream is currently active. No song queue is available.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return

        upcoming = list(player.queue._queue)

        if player.current is None and not upcoming:
            await ctx.send("The queue is empty.")
            return

        embed = discord.Embed(title="Music Queue", color=discord.Color.orange())

        if player.current:
            embed.add_field(
                name="Now Playing",
                value=f"**{player.current.title}**\n"
                      f"Mode: {player.current.mode.capitalize()} | "
                      f"[Link]({player.current.url})",
                inline=False,
            )
        else:
            embed.add_field(
                name="I'm singing an empty song.",
                value="Nothing is currently playing.",
                inline=False,
            )

        if upcoming:
            for idx, song in enumerate(upcoming, 1):
                embed.add_field(
                    name=f"{idx}. {song.title}",
                    value=f"Mode: {song.mode.capitalize()} | [Link]({song.url})",
                    inline=False,
                )
        else:
            embed.add_field(
                name="Up Next",
                value="No songs in the queue.",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command(name='pause')
    async def pause_(self, ctx):
        """Pause the current song."""
        player = self.get_player(ctx)

        if player.is_streaming:
            embed = discord.Embed(
                title="Cannot Pause Stream",
                description="Cannot pause while a stream is active.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if ctx.voice_client is None or not ctx.voice_client.is_playing():
            embed = discord.Embed(
                title=random.choice(["Silence...", "Already Quiet!", "Nothing to Pause!"]),
                description="No song is currently playing.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        ctx.voice_client.pause()

        embed = discord.Embed(
            title=random.choice(["Hold the Music!", "Paused!", "Intermission Time!"]),
            description="Playback paused.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name='resume')
    async def resume_(self, ctx):
        """Resume the paused song."""
        player = self.get_player(ctx)

        if player.is_streaming:
            embed = discord.Embed(
                title="Cannot Resume Stream",
                description="Cannot resume while a stream is active.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        if ctx.voice_client is None or not ctx.voice_client.is_paused():
            embed = discord.Embed(
                title=random.choice(["Keep Calm!", "Nothing to Resume!", "All Systems Go!"]),
                description="Playback is not paused.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        ctx.voice_client.resume()

        embed = discord.Embed(
            title=random.choice(["Music On!", "Let's Jam!", "And We're Back!"]),
            description="Playback resumed.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))