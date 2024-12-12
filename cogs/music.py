import discord
from discord.ext import commands
from discord import ui, Interaction
import random
from yt_dlp import YoutubeDL
import asyncio
import time

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
        'nightcore': 'asetrate=44100*1.24,aresample=44100',
        'slowed': 'asetrate=44100*0.85,aresample=44100',
    }

    def __init__(self, source, *, data, mode='normal'):
        self.source = source  # This is the FFmpegOpusAudio source
        self.data = data
        self.mode = mode
        self.title = data.get('title')
        self.url = data.get('webpage_url')
        self.duration = data.get('duration')
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
        self.volume = 0.8
        self.voice_client = ctx.voice_client
        self.start_time = None
        self.paused_time = None
        self.total_paused_duration = 0

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        while True:
            self.next.clear()
            self.start_time = time.time()
            try:
                # Wait for the next song in the queue
                try:
                    self.current = await self.queue.get()
                except asyncio.TimeoutError:
                    # Handle timeout and disconnect
                    embed = discord.Embed(
                        title="Party's Over!",
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
                custom_emoji = "<a:playing:1313630246049943563>"
                # Now Playing Embed
                embed = discord.Embed(
                    title=f"{custom_emoji} Now Playing ({self.current.mode.capitalize()} Mode)",
                    description=f"[{self.current.title}]({self.current.url})",
                    color=discord.Color.blue(),
                )
                embed.set_thumbnail(url=self.current.thumbnail)
                embed.set_author(
                    name=f"Requested by {self.current.requester}",
                    icon_url=getattr(self.current.requester.avatar, 'url', None)
                )

                # Create the View with player controls
                controls = PlayerControls(self)

                # Send the message with the embed and controls
                message = await self.channel.send(embed=embed, view=controls)

                # Wait until the song is finished
                await self.next.wait()

                # Disable the buttons after the song is over
                controls.disable_all_items()
                try:
                    await message.edit(view=controls)
                except discord.NotFound:
                    # Message might have been deleted
                    pass

                # Check if the queue is empty after the song finishes
                if self.queue.empty():
                    embed = discord.Embed(
                        title="All Done!",
                        description="Playback finished. Leaving the voice channel. You can start playing song again by using the `play`, `slowed` or `nightcore` command.",
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
class PlayerControls(ui.View):
    def __init__(self, player, *, timeout=None):
        super().__init__(timeout=timeout)
        self.player = player

    def disable_all_items(self):
        for item in self.children:
            item.disabled = True

    async def interaction_check(self, interaction: Interaction) -> bool:
        # Only allow users in the same voice channel to interact
        if interaction.user.voice and interaction.user.voice.channel == self.player.guild.voice_client.channel:
            return True
        else:
            await interaction.response.send_message(
                "You must be in the voice channel to use these controls.",
                ephemeral=True,
            )
            return False

    @ui.button(label='Pause', style=discord.ButtonStyle.primary, emoji='⏸️')
    async def pause(self, interaction: Interaction, button: ui.Button):
        if self.player.guild.voice_client.is_playing():
            self.player.guild.voice_client.pause()
            self.player.paused_time = time.time()  # Record when paused
            await interaction.response.send_message("Playback paused.", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is playing to pause.", ephemeral=True)

    @ui.button(label='Resume', style=discord.ButtonStyle.primary, emoji='▶️')
    async def resume(self, interaction: Interaction, button: ui.Button):
        if self.player.guild.voice_client.is_paused():
            self.player.guild.voice_client.resume()
            # Calculate paused duration
            paused_duration = time.time() - self.player.paused_time
            self.player.total_paused_duration += paused_duration
            self.player.paused_time = None
            await interaction.response.send_message("Playback resumed.", ephemeral=True)
        else:
            await interaction.response.send_message("Playback is not paused.", ephemeral=True)
            
    @ui.button(label='Skip', style=discord.ButtonStyle.primary, emoji='⏭️')
    async def skip(self, interaction: Interaction, button: ui.Button):
        if self.player.guild.voice_client.is_playing():
            self.player.skip()
            await interaction.response.send_message("Skipped the current song.", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is playing to skip.", ephemeral=True)
            
    @ui.button(label='Add Normal', style=discord.ButtonStyle.secondary, emoji='🎵', row=1)
    async def add_normal(self, interaction: Interaction, button: ui.Button):
        modal = AddSongModal(self.player, mode='normal')
        await interaction.response.send_modal(modal)

    @ui.button(label='Add Nightcore', style=discord.ButtonStyle.secondary, emoji='🎧', row=1)
    async def add_nightcore(self, interaction: Interaction, button: ui.Button):
        modal = AddSongModal(self.player, mode='nightcore')
        await interaction.response.send_modal(modal)

    @ui.button(label='Add Slowed', style=discord.ButtonStyle.secondary, emoji='🎼', row=1)
    async def add_slowed(self, interaction: Interaction, button: ui.Button):
        modal = AddSongModal(self.player, mode='slowed')
        await interaction.response.send_modal(modal)

    @ui.button(label='Stop', style=discord.ButtonStyle.danger, emoji='⏹️')
    async def stop(self, interaction: Interaction, button: ui.Button):
        await self.player.cleanup()
        await interaction.response.send_message("Player stopped and disconnected.", ephemeral=True)
        # Disable the buttons after stopping
        self.disable_all_items()
        await interaction.message.edit(view=self)

class AddSongModal(ui.Modal, title='Add Song'):
    def __init__(self, player, mode):
        super().__init__()
        self.player = player
        self.mode = mode

    song_input = ui.TextInput(
        label='Song Name or URL',
        placeholder='Enter song name or URL...',
        required=True
    )

    async def on_submit(self, interaction: Interaction):
        await interaction.response.defer()
        ctx = await interaction.client.get_context(interaction.message)
        
        try:
            source = await YTDLSource.create_source(
                ctx, 
                str(self.song_input), 
                loop=interaction.client.loop, 
                mode=self.mode
            )
            source.requester = interaction.user
            await self.player.queue.put(source)

            embed = discord.Embed(
                title="Added to Queue",
                description=f"[{source.title}]({source.url})",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=source.thumbnail)
            embed.set_footer(text=f"Mode: {self.mode.capitalize()} | Position in queue: {self.player.queue.qsize()}")
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"Error adding song: {str(e)}", ephemeral=True)


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

    def _format_duration(self, seconds):
        seconds = int(seconds)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02}:{seconds:02}"
        else:
            return f"{minutes}:{seconds:02}"

    def _create_progress_bar(self, elapsed, total, bar_length=20):
        if total == 0:
            return "🔘" + "─" * (bar_length - 1)
        progress = min(max(elapsed / total, 0), 1)
        pos = int(progress * bar_length)
        bar = "─" * bar_length
        bar = bar[:pos] + "🔘" + bar[pos + 1:]
        return f"`{bar}`"

    async def _create_now_playing_embed(self, player):
        current = player.current

        # Calculate elapsed time
        elapsed_time = time.time() - player.start_time - player.total_paused_duration
        elapsed_time = max(0, elapsed_time)  # Ensure non-negative

        # Format elapsed and total duration
        elapsed_str = self._format_duration(elapsed_time)
        total_duration = current.data.get('duration', 0)
        total_str = self._format_duration(total_duration)

        # Progress bar
        progress_bar = self._create_progress_bar(elapsed_time, total_duration)

        # Queue length
        queue_length = player.queue.qsize()

        embed = discord.Embed(
            title="Now Playing",
            description=f"[{current.title}]({current.url})",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=current.thumbnail)
        embed.add_field(name="Author", value=current.data.get('uploader', 'Unknown'), inline=True)
        embed.add_field(name="Duration", value=f"{elapsed_str} / {total_str}", inline=True)
        embed.add_field(name="Queue Length", value=queue_length, inline=True)
        embed.add_field(name="Progress", value=progress_bar, inline=False)

        controls = PlayerControls(player)

        # Combine the views
        combined_view = ui.View()
        for item in controls.children:
            combined_view.add_item(item)

        return embed, combined_view

    async def _update_progress_bar(self, player, message):
        while player.current:
            if player.guild.voice_client.is_paused():
                # If paused, wait until resumed
                await asyncio.sleep(1)
                continue
            # Update the embed
            embed = await self._create_now_playing_embed(player)
            try:
                await message.edit(embed=embed)
            except discord.NotFound:
                # Message was deleted
                break
            await asyncio.sleep(5)  # Update every 5 seconds

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
        self.player.paused_time = time.time()
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
                    # Calculate paused duration
        paused_duration = time.time() - self.player.paused_time
        self.player.total_paused_duration += paused_duration
        self.player.paused_time = None
        ctx.voice_client.resume()

        embed = discord.Embed(
            title=random.choice(["Music On!", "Let's Jam!", "And We're Back!"]),
            description="Playback resumed.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='nowplaying', aliases=['np'])
    async def now_playing(self, ctx):
        player = self.get_player(ctx)

        if not player.current or not ctx.voice_client or not ctx.voice_client.is_playing():
            embed = discord.Embed(
                title="Nothing is playing",
                description="There is no song currently playing.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        embed, view = await self._create_now_playing_embed(player)
        message = await ctx.send(embed=embed, view=view)
        await self._update_progress_bar(player, message)

async def setup(bot):
    await bot.add_cog(Music(bot))