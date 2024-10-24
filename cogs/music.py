# Made with ❤️ by Lunatico Annie. Status: Finished!

import discord
from discord.ext import commands
import yt_dlp
import asyncio
import random

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.8):
        super().__init__(source, volume=volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, current_mode="normal", timeout=20):
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '192',
            }],
            'postprocessor_args': [
                '-ar', '48000',
                '-ac', '2',
            ],
            'prefer_ffmpeg': True,
            'duration_min': 61,  # Exclude Shorts by requiring a minimum duration of 61 seconds
            'socket_timeout': 20,  # Increase timeout (seconds)
        }

        # Check if the query is a URL or not
        if not url.startswith(('http://', 'https://')):
            # If it's not a URL, perform a YouTube search using yt-dlp
            ydl_opts['default_search'] = 'ytsearch1'

        def extract_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Handle multiple entries and sort by view count
                if 'entries' in info:
                    info = sorted(info['entries'], key=lambda x: x.get('view_count', 0), reverse=True)[0]
                return info

        # Use asyncio to apply a timeout for yt-dlp extraction
        try:
            loop = loop or asyncio.get_event_loop()
            info = await asyncio.wait_for(loop.run_in_executor(None, extract_info), timeout)
        except asyncio.TimeoutError:
            print(f"Timeout after {timeout} seconds while fetching {url}")
            return None

        # Apply filters based on current_mode
        filters = None
        if current_mode == "nightcore":
            filters = '-filter:a "asetrate=44100*1.2,aresample=44100"'
        elif current_mode == "slowed":
            filters = '-filter:a "asetrate=44100*0.85,aresample=44100"'

        # FFmpeg options
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': filters if filters else '-vn'
        }

        return cls(discord.FFmpegPCMAudio(info['url'], **ffmpeg_options), data=info)

class Song:
    def __init__(self, title, url):
        self.title = title
        self.url = url

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []  # Normal queue
        self.slowed_queue = [] # Slowed queue
        self.nightcore_queue = []  # Nightcore queue
        self.is_streaming_mode = False
        self.current_mode = "normal"  # Flag to check current playback mode. Default is normal.
        self.genre_streams = {
            'lofi': ['https://www.youtube.com/live/jfKfPfyJRdk?si=-0LEOJqrjSQll2Fx', 'https://www.youtube.com/live/mwPR8aizAyo?si=513xFxn5evg2ky8I', 'https://www.youtube.com/live/ralJmHG-DII?si=yD21si4hfIssL-a6', 'https://www.youtube.com/live/7p41rWD3s-c?si=PrF1E8aPYQ3kFkCv'],

            'deep_house': ['https://youtu.be/cnVPm1dGQJc?si=5g08aZZPQl5c2mtn', 'https://youtu.be/DsAd2Brhr-M?si=mFBVQn77MpqvsrIj', 'https://youtu.be/ZiyYqg75v7Y?si=hGyWqzuRYNnbU6if', 'https://youtu.be/B-rrm46WGhE?si=hi23i1aLSs7GUmHG'],

            'hardstyle': ['https://youtu.be/U3ZxZEFo1lk?si=c1ExdwWLuem8jgJZ', 'https://youtu.be/I6Tgl33CAjc?si=20pUmynbbnB5Uuwt', 'https://youtu.be/QhYlAM40oUY?si=7ovc1y3ng_QEOwJ8'],

            'synthwave': ['https://www.youtube.com/live/4xDzrJKXOOY?si=2NgFq-GZqKm_ZNlu', 'https://www.youtube.com/live/UedTcufyrHc?si=ZAwoaD1tOAq6MrUp','https://www.youtube.com/live/5-anTj1QrWs?si=lNMP_kB4GsfPmYVY', 'https://www.youtube.com/live/KNJyQwgzrMg?si=WLjD3g0hzNBpFAKI', 'https://youtu.be/k3WkJq478To?si=rf_xpFYGhRZ0Wsay', 'https://youtu.be/cCTaiJZAZak?si=zu17yQiXAR_PYEO3'],

            'progressive_house': ['https://youtu.be/jaE6M5Lr0mo?si=gP8jpPGMBq7ZN2Fp', 'https://youtu.be/CEbXiuDKRlM?si=HN8Svh7AChUqxhx1', 'https://youtu.be/GQ3qAnkrLzI?si=OcAcK0A_TLN_fMR4', 'https://youtu.be/8NsEHIU_iuE?si=lqEvAlpcEJEHcSkK', 'https://youtu.be/jaE6M5Lr0mo?si=gP8jpPGMBq7ZN2Fp', 'https://youtu.be/CEbXiuDKRlM?si=HN8Svh7AChUqxhx1', 'https://youtu.be/GQ3qAnkrLzI?si=OcAcK0A_TLN_fMR4', 'https://youtu.be/8NsEHIU_iuE?si=lqEvAlpcEJEHcSkK'],

            'kw_futurebass': ['https://youtu.be/urm1kR7vewM?si=Kw79owZnW_IPZZcO', 'https://youtu.be/tGhEMlxrjA8?si=gNdEuXSCYx2yyI5p', 'https://youtu.be/Ym0WFiHMuyw?si=IwixdnzpYEfDhlPS', 'https://youtu.be/iTyKy_AvhPM?si=PztjS99leqWIjhXn','https://youtu.be/Ym0WFiHMuyw?si=4b-zeuB5OzzwGZVX', 'https://youtu.be/0zYsGzdwfjg?si=PizQPEZMAlHgW89s', 'https://youtu.be/iTyKy_AvhPM?si=BYPq4-k1VFtpwvWA'],
        }
# Updated on_song_finished function to check when a song ends
    def on_song_finished(self, ctx):
        """Callback when the current song finishes."""
        if ctx.voice_client and not ctx.voice_client.is_playing():
            self.play_next(ctx)

# Optimized play_next function
    def play_next(self, ctx):
        """Plays the next song in the appropriate queue, switching modes if necessary."""
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            return  # Skip if already playing or paused

        next_song = None

        # Try selecting a song from the current mode's queue
        if self.current_mode == "nightcore" and self.nightcore_queue:
            next_song = self.nightcore_queue.pop(0)
        elif self.current_mode == "slowed" and self.slowed_queue:
            next_song = self.slowed_queue.pop(0)
        elif self.queue:
            next_song = self.queue.pop(0)

        # If the current queue is empty, switch to another queue if available
        if next_song is None:
            if self.current_mode == "nightcore" and not self.nightcore_queue:
                if self.slowed_queue:
                    self.current_mode = "slowed"
                    next_song = self.slowed_queue.pop(0)
                elif self.queue:
                    self.current_mode = "normal"
                    next_song = self.queue.pop(0)

            elif self.current_mode == "slowed" and not self.slowed_queue:
                if self.nightcore_queue:
                    self.current_mode = "nightcore"
                    next_song = self.nightcore_queue.pop(0)
                elif self.queue:
                    self.current_mode = "normal"
                    next_song = self.queue.pop(0)

            elif self.current_mode == "normal" and not self.queue:
                if self.nightcore_queue:
                    self.current_mode = "nightcore"
                    next_song = self.nightcore_queue.pop(0)
                elif self.slowed_queue:
                    self.current_mode = "slowed"
                    next_song = self.slowed_queue.pop(0)

        # If no songs are found in any queue, send a message
        if next_song is None:
            self.current_mode = "normal"
            embed = discord.Embed(
                title="Queue Empty",
                description="All queues are empty. No more songs to play.",
                color=discord.Color.orange()
            )
            asyncio.run_coroutine_threadsafe(ctx.send(embed=embed), self.bot.loop).result()
            return

        # Debugging statement to confirm mode and song
        print(f"Playing next song in mode: {self.current_mode}, Song: {next_song.title}")

        # Play the selected song
        try:
            ctx.voice_client.play(next_song, after=lambda e: self.on_song_finished(ctx))
            embed = discord.Embed(
                title=f'Now playing in {self.current_mode.capitalize()} mode',
                description=f'[{next_song.title}]({next_song.data.get("webpage_url")})',
                color=discord.Color.blue()
            )
            if next_song.data.get('thumbnail'):
                embed.set_thumbnail(url=next_song.data.get('thumbnail'))
            fut = asyncio.run_coroutine_threadsafe(ctx.send(embed=embed), self.bot.loop)
            fut.result()
        except Exception as e:
            print(f"Error playing next song: {e}")


    @commands.command(name="play")
    async def play(self, ctx, *, query=None):
        """Plays a song from YouTube (can be URL or search query)."""
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                return

        if self.is_streaming_mode:
            embed = discord.Embed(title="Unavailable", description="The bot is currently in 24/7 streaming mode. You can't add new songs.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return


        async with ctx.typing():
            try:
                player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True, current_mode=self.current_mode)
            except Exception as e:
                print(f"Error fetching the song: {e}")
                return


        if ctx.voice_client.is_playing():
            self.queue.append(player)
            embed = discord.Embed(title="Added to queue", description=f'[{player.title}]({player.data.get("webpage_url")})', color=discord.Color.green())
            await ctx.send(embed=embed)
            return

        try:
            ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))
            embed = discord.Embed(title='Now playing', description=f'[{player.title}]({player.data.get("webpage_url")})', color=discord.Color.blue())
            thumbnail_url = player.data.get('thumbnail')
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred while playing the song: {e}")
            print(f"Error playing the song: {e}")
            return
    
    # Optimized nightcore command
    @commands.command(name="nightcore")
    async def nightcore(self, ctx, *, query=None):
        """Plays a song in Nightcore mode (can be URL or search query)."""
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                return

        if self.is_streaming_mode:
            embed = discord.Embed(title="Unavailable", description="The bot is currently in 24/7 streaming mode. You can't add new songs.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        async with ctx.typing():
            try:
                player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True, current_mode="nightcore")
            except Exception as e:
                await ctx.send(f"An error occurred while fetching the song: {e}")
                print(f"Error fetching the song: {e}")
                return

        if ctx.voice_client.is_playing():
            self.nightcore_queue.append(player)
            embed = discord.Embed(title="Added to Nightcore queue", description=f'[{player.title}]({player.data.get("webpage_url")})', color=discord.Color.green())
            await ctx.send(embed=embed)
            return

        try:
            ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))
            embed = discord.Embed(title='Now playing in Nightcore mode', description=f'[{player.title}]({player.data.get("webpage_url")})', color=discord.Color.blue())
            thumbnail_url = player.data.get('thumbnail')
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred while playing the song: {e}")
            print(f"Error playing the song: {e}")
            return

    @commands.command(name="slowed")
    async def slowed(self, ctx, *, query=None):
        """Plays a song in Slowed mode (can be URL or search query)."""
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                return

        if self.is_streaming_mode:
            embed = discord.Embed(title="Unavailable", description="The bot is currently in 24/7 streaming mode. You can't add new songs.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        async with ctx.typing():
            try:
                player = await YTDLSource.from_url(query, loop=self.bot.loop, stream=True, current_mode="slowed")
            except Exception as e:
                await ctx.send(f"An error occurred while fetching the song: {e}")
                print(f"Error fetching the song: {e}")
                return

        if ctx.voice_client.is_playing():
            self.slowed_queue.append(player)
            embed = discord.Embed(title="Added to Slowed queue", description=f'[{player.title}]({player.data.get("webpage_url")})', color=discord.Color.green())
            await ctx.send(embed=embed)
            return

        try:
            ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))
            embed = discord.Embed(title='Now playing in Slowed mode', description=f'[{player.title}]({player.data.get("webpage_url")})', color=discord.Color.blue())
            thumbnail_url = player.data.get('thumbnail')
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred while playing the song: {e}")
            print(f"Error playing the song: {e}")
            return

    @commands.command(name="toggle_effects")
    async def toggle_effects(self, ctx, mode: str = None):
        """
        Toggle between Normal, Nightcore, and Slowed modes, or switch to the specified mode.
    
        Usage:
        - am/toggle_effects -> Automatically switch between modes.
        - am/toggle_effects normal -> Switches to normal mode.
        - am/toggle_effects nightcore -> Switches to nightcore mode.
        - am/toggle_effects slowed -> Switches to slowed mode.
        """
    
        valid_modes = ["normal", "nightcore", "slowed"]
    
        # Normalize mode input
        if mode:
            mode = mode.lower()

    # If no mode is provided, cycle through the modes
        if mode is None:
            if self.current_mode == "normal":
                self.current_mode = "nightcore"
                response = "Switched to Nightcore mode."
            elif self.current_mode == "nightcore":
                self.current_mode = "slowed"
                response = "Switched to Slowed mode."
            else:
                self.current_mode = "normal"
                response = "Switched to Normal mode."
    
    # Switch to the specified mode
        elif mode in valid_modes:
            self.current_mode = mode
            response = f"Switched to {mode.capitalize()} mode."
    
        else:
            response = f"Invalid mode! Choose from: {', '.join(valid_modes)}"

    # Send confirmation to the user
        embed = discord.Embed(title="Mode Changed", description=response, color=discord.Color.green())
        await ctx.send(embed=embed)
    
    # Apply the appropriate flag depending on the selected mode
        if self.current_mode == "normal":
            self.current_mode = "normal"
            
        elif self.current_mode == "nightcore":
            self.current_mode = "nightcore"
            
        elif self.current_mode == "slowed":
            self.current_mode = "slowed"


    @commands.command(name="stop")
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice."""
        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            embed = discord.Embed(title="Ahem! Hold up!", description="I'm not connected to a voice channel.", color=discord.Color.yellow())
            await ctx.send(embed=embed)
            return

        if self.is_streaming_mode:
            embed = discord.Embed(title="Hold up!", description="You cannot use this command when streaming mode is active. Consider using `stopstream` command instead.", color=discord.Color.brand_red())
            await ctx.send(embed=embed) # Prevent this command from executing if streaming mode is True (or active).
            return

        self.queue.clear()
        self.nightcore_queue.clear()
        self.slowed_queue.clear()
        self.current_mode = "normal"
        await ctx.voice_client.disconnect()
        embed = discord.Embed(title="Stopped", description="Stopped music and disconnected.", color=discord.Color.green())
        await ctx.send(embed=embed)


    @commands.command(name="queue")
    async def queue(self, ctx):
        """Displays all current song queues."""
        if not self.queue and not self.nightcore_queue and not self.slowed_queue:
            embed = discord.Embed(title="Queue", description="All queues are currently empty.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        if self.is_streaming_mode:
            embed = discord.Embed(title="Unavailable", description="This command is unavailable when streaming mode is active.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(title="Music Queue", color=discord.Color.blue())

    # Add normal queue songs to the embed
        if self.queue:
            normal_queue_desc = "\n".join([f"{i + 1}. [{song.title}]({song.data.get('webpage_url')})" for i, song in enumerate(self.queue)])
            embed.add_field(name="Normal Queue", value=normal_queue_desc, inline=False)

    # Add nightcore queue songs to the embed
        if self.nightcore_queue:
            nightcore_queue_desc = "\n".join([f"{i + 1}. [{song.title}]({song.data.get('webpage_url')})" for i, song in enumerate(self.nightcore_queue)])
            embed.add_field(name="Nightcore Queue", value=nightcore_queue_desc, inline=False)

    # Add slowed queue songs to the embed
        if self.slowed_queue:
            slowed_queue_desc = "\n".join([f"{i + 1}. [{song.title}]({song.data.get('webpage_url')})" for i, song in enumerate(self.slowed_queue)])
            embed.add_field(name="Slowed Queue", value=slowed_queue_desc, inline=False)

        await ctx.send(embed=embed)

        
    @commands.command(name="stream")
    async def stream(self, ctx, genre=None):
        """Starts 24/7 streaming mode for a specific genre."""

    # Check if the genre is valid
        if genre is None or genre.lower() not in self.genre_streams:
            available_genres = ', '.join(self.genre_streams.keys())
            embed = discord.Embed(title="Genre List", description=f"Here are available genres: {available_genres}", color=discord.Color.blue())
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(title="Stream Mode!", description=f"Starting 24/7 {genre} stream!", color=discord.Color.green())
        await ctx.send(embed=embed)
    # Join the voice channel if not already connected
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                return

    # Stop any currently playing audio
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
    
    # Enable streaming mode
        self.is_streaming_mode = True
        self.queue.clear()  # Clear the regular song queue

    # Select a random stream URL from the genre's list
        genre_urls = self.genre_streams[genre.lower()]
        random_url = random.choice(genre_urls)

    # Play the stream immediately
        await self.play_stream(ctx, random_url, genre)

    async def play_stream(self, ctx, url, genre):
        """Plays the given stream URL."""
        async with ctx.typing():
            try:
            # Fetch the audio source
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            
            # Check if the player is None (invalid source)
                if player is None:
                    raise ValueError(f"Could not retrieve an audio source for URL: {url}")
            
            # Play the audio source
                ctx.voice_client.play(player, after=lambda e: self.play_next_genre_stream(ctx, genre) if e is None else print(f'Error: {e}'))

            except Exception as e:
            # Log the error and send feedback to the user
                print(f"Error while trying to play the stream: {e}")
                
    def play_next_genre_stream(self, ctx, genre):
        """Plays the next stream URL in the same genre."""
        # Check if the bot is still connected and if voice_client exists
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            print("Bot is not connected to a voice channel. Stopping stream.")
            return

        if self.is_streaming_mode and genre in self.genre_streams:

        
            try:
            # Run the coroutine thread-safely on the bot's loop
                # Pick the next random stream URL from the genre's list
                next_stream_url = random.choice(self.genre_streams[genre])

            # Create a coroutine for playing the stream
                coro = self.play_stream(ctx, next_stream_url, genre)
                fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                fut.result()  # Wait for the coroutine to finish and raise exceptions if any
            except Exception as e:
                print(f'Error occurred while playing next stream: {e}')


    @commands.command(name="stopstream")
    async def stopstream(self, ctx):
        """Stops the current stream and exits streaming mode."""
        if not self.is_streaming_mode:
            embed = discord.Embed(title="Error", description="The bot is not currently in streaming mode.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
    
        self.is_streaming_mode = False
        self.queue.clear()

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()  # Stop the current playing stream
        
        await asyncio.sleep(0.5)  # Delay to allow FFmpeg to clean up
    
    # Optionally, forcibly terminate the FFmpeg process (possible?)
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.cleanup()  # This should clean up the source, if implemented
            ctx.voice_client.source = None  # Clear the source

        if ctx.voice_client:
            await ctx.voice_client.disconnect(force=True)  # Use force to disconnect

        embed = discord.Embed(title="Stream Stopped", description="Stopped streaming and exited streaming mode.", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(name="pause")
    async def pause(self, ctx):
        """Pauses the currently playing song."""
        if ctx.voice_client is None or not ctx.voice_client.is_connected(): # Where do you want the bot to go??
            embed = discord.Embed(title="Pause where?", description="I'm not connected to a voice channel.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        
        if not ctx.voice_client.is_playing():
            embed = discord.Embed(title="Pause...what?", description="I'm not playing anything at the moment.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            embed = discord.Embed(title="La la la l-", description="Paused the song.", color=discord.Color.yellow())
            await ctx.send(embed=embed)

    @commands.command(name="resume")
    async def resume(self, ctx):
        """Resumes the paused song."""
        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            embed = discord.Embed(title="Ahem! Hold up!", description="I'm not connected to a voice channel.", color=discord.Color.yellow())
            await ctx.send(embed=embed)
            return

    # Check if the bot is paused
        if not ctx.voice_client.is_paused():
            embed = discord.Embed(title="Resume?", description="There's nothing to resume. I'm not paused.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return
        if ctx.voice_client.is_paused():
                ctx.voice_client.resume()
                embed = discord.Embed(title="-a la la la.", description="Resumed the song", color=discord.Color.yellow())
                await ctx.send(embed=embed)
    @commands.command(name="volume")
    async def volume(self, ctx, volume: int):
        """Changes the player's volume. Volume should be between 0 and 100."""
    
    # Check if the user is in a voice channel
        if not ctx.voice_client:
            embed = discord.Embed(title="Ahem. Hold up", description="I'm not connected to a voice channel", color=discord.Color.yellow())
            await ctx.send(embed=embed)
            return

        if ctx.voice_client.source is None:
            embed = discord.Embed(title="Uh...", description="I'm not playing anything at the moment.", color=discord.Color.yellow())
            await ctx.send(embed=embed)
            return

    # Ensure volume is within the valid range (0 to 100)
        if volume < 0 or volume > 100:
            embed = discord.Embed(title="Invalid value", description="Please provide a volume between 0 and 100.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
    
    # Convert the volume to a 0.0 - 1.0 range for ffmpeg
        ctx.voice_client.source.volume = volume / 100.0
        embed = discord.Embed(title="Success", description=f"Volume has been set to {volume}%.", color=discord.Color.blurple())
        await ctx.send(embed=embed)


    @play.before_invoke
    @nightcore.before_invoke
    @slowed.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                embed = discord.Embed(title="Ahem. Hold up!", description="You are not connected to a voice channel.", color=discord.Color.yellow())
                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MusicCog(bot))