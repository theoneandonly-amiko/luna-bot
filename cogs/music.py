# music_cog.py
import discord
from discord.ext import commands
import asyncio
import yt_dlp as youtube_dl
from collections import deque

# Suppress yt-dlp warnings
youtube_dl.utils.bug_reports_message = lambda: ''

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': '-',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'cookiefile': 'cookies.txt',  # If using cookies
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    },
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'opus',
        'preferredquality': '192',
    }],
    'extractor_args': {
        'youtube': {
            'skip': ['dash', 'hls']
        }
    },
    'postprocessor_args': [
        '-http_chunk_size', '10M'
    ],
    'age_limit': 0,
    'geo_bypass': True,
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
    'options': '-vn -c:a libopus -b:a 128k -application lowdelay -frame_duration 20',
}

ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

class YTDLSource(discord.AudioSource):
    def __init__(self, source, data):
        self.source = source
        self.title = data.get('title') or 'Unknown Title'
        self.url = data.get('url') or data.get('webpage_url')

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            if 'entries' in data:
                data = data['entries'][0]
            return cls(discord.FFmpegOpusAudio(data['url'], **FFMPEG_OPTIONS), data=data)
        except Exception as e:
            print(f'YTDL Error: {e}')
            raise commands.CommandError(f"Couldn't process audio: {e}")

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = deque()
        self.current_song = None
        self.volume = 0.9

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Music cog ready!')

    async def play_next(self, ctx):
        try:
            if self.song_queue:
                self.current_song = self.song_queue.popleft()
                ctx.voice_client.play(
                    self.current_song.source,
                    after=lambda e: asyncio.run_coroutine_threadsafe(
                        self.play_next(ctx), self.bot.loop
                ))
                await ctx.send(f'**Now playing:** {self.current_song.title}')
            else:
                await self.auto_disconnect(ctx)
        except Exception as e:
            print(f'Playback error: {e}')
            await self.play_next(ctx)  # Skip to next song on error
            
    async def auto_disconnect(self, ctx):
        await asyncio.sleep(300)  # 5 minutes
        if ctx.voice_client and not ctx.voice_client.is_playing():
            await ctx.voice_client.disconnect()
    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx, *, url):
        """Play music from YouTube"""
        if not ctx.author.voice:
            await ctx.send("You're not in a voice channel!")
            return
            
        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.voice_client.move_to(ctx.author.voice.channel)
        else:
            await ctx.author.voice.channel.connect()

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            self.song_queue.append(player)
            
            if not ctx.voice_client.is_playing():
                await self.play_next(ctx)
            else:
                await ctx.send(f'**Added to queue:** {player.title}')

    @commands.command(name='queue', aliases=['q'])
    async def queue(self, ctx):
        """Show the current queue"""
        if len(self.song_queue) == 0:
            return await ctx.send('Queue is empty!')
            
        queue_list = [f'{i+1}. {song.title}' for i, song in enumerate(self.song_queue)]
        await ctx.send('**Current queue:**\n' + '\n'.join(queue_list))

    @commands.command(name='skip')
    async def skip(self, ctx):
        """Skip the current song"""
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send('⏭ Skipped current song')
            await self.play_next(ctx)
        else:
            await ctx.send('Nothing is playing!')

    @commands.command(name='stop')
    async def stop(self, ctx):
        """Stop the bot and clear the queue"""
        self.song_queue.clear()
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send('⏹ Stopped playback')

    @commands.command(name='pause')
    async def pause(self, ctx):
        """Pause the current song"""
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send('⏸ Paused')

    @commands.command(name='resume')
    async def resume(self, ctx):
        """Resume paused playback"""
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send('▶ Resumed')


    @commands.command(name='nowplaying', aliases=['np'])
    async def nowplaying(self, ctx):
        """Show currently playing song"""
        if self.current_song:
            await ctx.send(f'**Now playing:** {self.current_song.title}\n{self.current_song.url}')
        else:
            await ctx.send('Nothing is currently playing!')

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You're not connected to a voice channel!")
                raise commands.CommandError("Author not connected to voice channel")

async def setup(bot):
    await bot.add_cog(MusicCog(bot))