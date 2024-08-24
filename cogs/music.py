import discord
from discord.ext import commands

# ================ Music Function ======================


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def from_query(cls, query, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        ytdl_format_options = {
        'format': 'bestaudio',
        'noplaylist': 'True',
        }
        ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

    # Regular expression to check if the query is a URL
        url_regex = re.compile(
            r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$'
        )

        try:
            if url_regex.match(query):            
            #Directly extract info from the URL
                info = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
            else:            
            # If not URL, treat it as a search query
                search_query = f"ytsearch:{query}"
                info = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False)['entries'][0])

            # Log: Display fetched information

            if not info:
                raise commands.CommandError("No results found for the provided query.")

            url = info.get('url')
            title = info.get('title')
            thumbnail = info.get('thumbnail')
            webpage_url = info.get('webpage_url')
            data = {'title': title, 'url': webpage_url, 'thumbnail': thumbnail}
    
            return cls(discord.FFmpegPCMAudio(url), data=data)

        except yt_dlp.utils.DownloadError as e:
            raise commands.CommandError(f"Download error: {e}")
        except IndexError:
            raise commands.CommandError("No results found. Please try a different query or URL.")
        except Exception as e:
        # Log the exact error
            print(f"An unexpected error occurred: {str(e)}")
            raise commands.CommandError(f"An unexpected error occurred: {str(e)}")
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        ytdl_format_options = {
            'format': 'bestaudio/best',
            'noplaylist': 'True',
        }
        ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

        info = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in info:
            info = info['entries'][0]

        data = {
            'title': info.get('title'),
            'url': info.get('url'),
        }

        if stream:
            return cls(discord.FFmpegPCMAudio(info['url']), data=data)
        else:
            return cls(discord.FFmpegPCMAudio(info['url']), data=data)
        

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.IDLE_TIMEOUT = 30
        self.current_player = None
        self.volume_level = 0.8  # Default volume level
        self.last_channel = None # Store the last active channel
        self.streaming_mode = False
        self.genre_urls = {
            'lofi': ['https://www..com/watch?v=jfKfPfyJRdk'],

            'deep_house': ['https://youtu.be/cnVPm1dGQJc?si=5g08aZZPQl5c2mtn', 'https://youtu.be/DsAd2Brhr-M?si=mFBVQn77MpqvsrIj', 'https://youtu.be/ZiyYqg75v7Y?si=hGyWqzuRYNnbU6if', 'https://youtu.be/B-rrm46WGhE?si=hi23i1aLSs7GUmHG'],

            'hardstyle': ['https://youtu.be/U3ZxZEFo1lk?si=c1ExdwWLuem8jgJZ', 'https://youtu.be/I6Tgl33CAjc?si=20pUmynbbnB5Uuwt', 'https://youtu.be/QhYlAM40oUY?si=7ovc1y3ng_QEOwJ8'],

            'synthwave': ['https://youtu.be/k3WkJq478To?si=rf_xpFYGhRZ0Wsay', 'https://youtu.be/cCTaiJZAZak?si=zu17yQiXAR_PYEO3',],

            'progressive_house': ['https://youtu.be/jaE6M5Lr0mo?si=gP8jpPGMBq7ZN2Fp', 'https://youtu.be/CEbXiuDKRlM?si=HN8Svh7AChUqxhx1', 'https://youtu.be/GQ3qAnkrLzI?si=OcAcK0A_TLN_fMR4', 'https://youtu.be/8NsEHIU_iuE?si=lqEvAlpcEJEHcSkK'],
            # Add more genres and URLs as needed
        }

    async def ensure_voice(self, ctx):
        if ctx.author.voice:
            if ctx.voice_client:
                if ctx.voice_client.channel != ctx.author.voice.channel:
                    await ctx.voice_client.move_to(self, ctx.author.voice.channel)
            else:
                await ctx.author.voice.channel.connect()
                last_active_channel = ctx.channel
        else:
            await ctx.send("You are not connected to a voice channel.", delete_after=20)

    
    @commands.command(name='play', help='Joins the voice channel and plays a song')
    async def play(self, ctx, *, query):
        self.last_channel = ctx.channel  
        await self.ensure_voice(self, ctx)

        if streaming_mode:
            embed = discord.Embed(title="Streaming Mode", description="Cannot add songs while in 24/7 streaming mode.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        async with ctx.typing():
            player = await YTDLSource.from_query(query, loop=bot.loop)
            player.volume = volume_level  # Set the volume
            queue.append(player)

            if not ctx.voice_client.is_playing():
                await play_next_song(self, ctx)
            else:
                embed = discord.Embed(title="Added to Queue", description=f'[{player.title}]({player.url})', color=discord.Color.blue())
                if player.thumbnail:
                    embed.set_thumbnail(url=player.thumbnail)
                await ctx.send(embed=embed)

    async def play_next_song(self, ctx):

        if len(queue) > 0:
            player = queue.pop(0)
            self.current_player = player

            if ctx.voice_client.is_connected():  # Ensure bot is still connected
                ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(ctx), bot.loop))

            embed = discord.Embed(title="Now Playing", description=f'[{player.title}]({player.url})', color=discord.Color.green())
            embed.set_thumbnail(url=player.data['thumbnail'])  # Display the thumbnail
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Queue", description="Queue is empty.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            await check_idle_disconnect(ctx)

    async def check_idle_disconnect(self, ctx):
        await asyncio.sleep(IDLE_TIMEOUT)  # Wait for the idle timeout
        if ctx.voice_client and not ctx.voice_client.is_playing() and not queue:
            await ctx.voice_client.disconnect()
            embed = discord.Embed(title="Disconnected", description="Disconnected due to inactivity.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name='pause', help='This command pauses the song')
    async def pause(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            embed = discord.Embed(title="Paused", description="The song has been paused.", color=discord.Color.yellow())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Error", description="The bot is not playing anything at the moment.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name='resume', help='Resumes the song')
    
    async def resume(self, ctx):
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            embed = discord.Embed(title="Resumed", description="The song has been resumed.", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Error", description="The bot was not playing anything before this. Use play command", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name='stop', help='Stops the currently playing song')
    
    async def stop(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            embed = discord.Embed(title="Stopped", description="The current song has been stopped.", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Error", description="The bot is not playing anything at the moment.", color=discord.Color.red())
            await ctx.send(embed=embed)
        await check_idle_disconnect(self, ctx)

    @commands.command(name='queue', help='Displays the current song queue')
    
    async def display_queue(self, ctx):
        if len(queue) > 0:
            queue_list = "\n".join([f"{i + 1}. [{song.title}]({song.url})" for i, song in enumerate(queue)])
            embed = discord.Embed(title="Current Queue", description=f"{queue_list}", color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Queue", description="The queue is empty.", color=discord.Color.orange())
            await ctx.send(embed=embed)

    @commands.command(name='skip', help='Skips the current song')
    
    async def skip(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            embed = discord.Embed(title="Skipped", description="The current song has been skipped.", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Error", description="The bot is not playing anything at the moment.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command(name='volume_up', help='Increases the volume by 10%')
    
    async def volume_up(self, ctx):
        global volume_level
        if volume_level < 1.0:
            volume_level = min(volume_level + 0.1, 1.0)
            if current_player:
                current_player.volume = volume_level
            embed = discord.Embed(title="Volume Up", description=f'Volume increased to {int(volume_level * 100)}%', color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Volume", description='Volume is already at maximum.', color=discord.Color.orange())
            await ctx.send(embed=embed)

    @commands.command(name='volume_down', help='Decreases the volume by 10%')
    
    async def volume_down(self, ctx):
        global volume_level
        if volume_level > 0.0:
            volume_level = max(volume_level - 0.1, 0.0)
            if current_player:
                current_player.volume = volume_level
            embed = discord.Embed(title="Volume Down", description=f'Volume decreased to {int(volume_level * 100)}%', color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Volume", description='Volume is already at minimum.', color=discord.Color.orange())
            await ctx.send(embed=embed)

    @commands.command(name='clear_queue', help='Clears the entire music queue')
    
    async def clear_queue(self, ctx):
        global queue

        if len(queue) > 0:
            queue.clear()


            embed = discord.Embed(title="Queue Cleared", description="The music queue has been cleared.", color=discord.Color.red())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Queue Empty", description="The queue is already empty.", color=discord.Color.orange())
            await ctx.send(embed=embed)

    @commands.command(name='disconnect', help='Disconnects the bot from the voice channel')
    
    async def disconnect(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()

            # Clear the queue and reset variables
            queue.clear()
            global current_player, streaming_mode
            current_player = None
            streaming_mode = False

            embed = discord.Embed(title="Disconnected", description="Disconnected from the voice channel.", color=discord.Color.green())
            await ctx.send(embed=embed, delete_after=20)
        else:
            embed = discord.Embed(title="Idling", description="I'm not connected to any voice channel.", color=discord.Color.red())
            await ctx.send(embed=embed, delete_after=20)

    @commands.command(name='stream247', help='Starts streaming the chosen genre 24/7')
    
    async def start_stream(self, ctx, genre: str):
        global streaming_mode
        streaming_mode = True
        await self.ensure_voice(self, ctx)

        genre = genre.lower()
        if genre not in genre_urls:
            await ctx.send(f"Invalid genre. Available genres are: {', '.join(genre_urls.keys())}")
            return

        playlist = genre_urls[genre]
        embed = discord.Embed(title="Now Playing", description=f"Streaming {genre.capitalize()} music 24/7", color=discord.Color.green())
        await ctx.send(embed=embed)
        async def play_next_video():
            if not ctx.voice_client:
                return  # Ensure the bot is still connected to a voice channel before playing the next video.

            video_url = random.choice(playlist)

            try:
                player = await YTDLSource.from_url(video_url, loop=self.bot.loop, stream=True)
                if ctx.voice_client:
                    ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_video(), self.bot.loop))
            except Exception as e:
                print(f"Error playing video: {e}")
                embed = discord.Embed(title='Error', description='An error occurred while trying to start the stream.', color=discord.Color.red())
                await ctx.send(embed=embed)

        await play_next_video()  # Start playing the first video in the playlist

        while streaming_mode:
            if not ctx.voice_client or not ctx.voice_client.is_playing():
                await play_next_video()
            await asyncio.sleep(5)  # Check every 5 seconds if the stream has stopped

    @commands.command(name='stop247', help='Stops the 24/7 streaming.')
    async def stop_streaming(self, ctx):
        global streaming_mode
        streaming_mode = False

        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()  # Stop the current streaming video

            # Clear any remaining videos in the queue
            queue.clear()
        else:
            await ctx.send(embed=discord.Embed(title="Error", description="The bot is not streaming anything at the moment.", color=discord.Color.red()))

        if ctx.voice_client and ctx.voice_client.is_connected():
            await ctx.voice_client.disconnect()  # Optionally, disconnect from the voice channel
            await ctx.send(embed=discord.Embed(title="Streaming Stopped", description="Exited 24/7 streaming mode.", color=discord.Color.red()))

async def setup(bot):
    await bot.add_cog(Music(bot))