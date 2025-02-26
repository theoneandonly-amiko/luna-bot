import discord
from discord.ext import commands
import yt_dlp
import asyncio
import random
from enum import Enum
from datetime import datetime, timezone, timedelta

YTDLP_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'max_downloads': 1,
    #'quiet': True,
    'noplaylist': True,
    'no_warnings': True,
    'source_address': '0.0.0.0',
    'cookiefile': 'cogs/cookies.txt',
    'extractor_args': {
        'soundcloud': {
            'client_id': 'akcDl6lB9RfwyhLSb2Xw2MwPR3Ow85Kr'
        }
    }
}


FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
    'options': '-vn -bufsize 64k'
}
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = {}
        self.now_playing = {}
        self.ytdlp = yt_dlp.YoutubeDL(YTDLP_OPTIONS)
        self.loop_mode = {}  # None, 'song', 'queue'

    async def play_next(self, ctx):
        try:
            if not ctx.voice_client:
                return
                
            if ctx.guild.id in self.loop_mode and ctx.guild.id in self.now_playing:
                current_track = self.now_playing[ctx.guild.id]
                
                # Song loop - keep playing the same track
                if self.loop_mode[ctx.guild.id] == 'song':
                    source = discord.FFmpegPCMAudio(current_track['url'], **FFMPEG_OPTIONS)
                    ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
                    return
                    
                # Queue loop - add current track to end of queue
                elif self.loop_mode[ctx.guild.id] == 'queue':
                    self.queue[ctx.guild.id].append(current_track)

            if ctx.guild.id in self.queue and self.queue[ctx.guild.id]:
                next_track = self.queue[ctx.guild.id].pop(0)
                source = discord.FFmpegPCMAudio(next_track['url'], **FFMPEG_OPTIONS)
                ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
                self.now_playing[ctx.guild.id] = next_track
                
                embed = discord.Embed(
                    title="Now Playing",
                    description=f"[{next_track['title']}]({next_track['webpage_url']})",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                if next_track.get('thumbnail'):
                    embed.set_thumbnail(url=next_track['thumbnail'])
                embed.add_field(name="Duration", value=str(timedelta(seconds=next_track['duration'])))
                embed.add_field(name="Platform", value=next_track['platform'].title())
                embed.add_field(name="Requested by", value=next_track['requester'].mention)
                await ctx.send(embed=embed)
                
        except Exception as e:
            await ctx.send(f"Playback error occurred. Attempting to play next track.")
            await self.play_next(ctx)
    async def handle_playback_error(self, error, ctx):
        if error:
            await self.play_next(ctx)    
    
    @commands.command()
    async def play(self, ctx, platform: str, *, query):
        """Plays audio from selected platform or adds it to queue"""
        platform = platform.lower()
        if platform not in ['youtube', 'soundcloud']:
            await ctx.send("Please specify either 'youtube' or 'soundcloud' as the platform!")
            return

        search_prefix = 'ytsearch' if platform == 'youtube' else 'scsearch'

        if not ctx.author.voice:
            await ctx.send("You need to be in a voice channel first!")
            return

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        async with ctx.typing():
            try:
                is_url = any(s in query.lower() for s in ['youtube.com', 'youtu.be', 'soundcloud.com'])
                if not is_url:
                    query = f"{search_prefix}:{query}"

                data = await self.bot.loop.run_in_executor(None, lambda: self.ytdlp.extract_info(query, download=False))
                
                if 'entries' in data:
                    data = data['entries'][0]

                track_info = {
                    'url': data['url'],
                    'title': data['title'],
                    'webpage_url': data.get('webpage_url', 'No URL available'),
                    'thumbnail': data.get('thumbnail'),
                    'duration': data['duration'],
                    'platform': platform,
                    'requester': ctx.author
                }

                if ctx.voice_client.is_playing():
                    if ctx.guild.id not in self.queue:
                        self.queue[ctx.guild.id] = []
                    self.queue[ctx.guild.id].append(track_info)
                    await ctx.send(f"Added to queue: **{data['title']}**")
                else:
                    source = discord.FFmpegPCMAudio(track_info['url'], **FFMPEG_OPTIONS)
                    ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
                    self.now_playing[ctx.guild.id] = track_info
                    
                    embed = discord.Embed(
                        title="Now Playing",
                        description=f"[{track_info['title']}]({track_info['webpage_url']})",
                        color=discord.Color.green(),
                        timestamp=datetime.now(timezone.utc)
                    )
                    if track_info.get('thumbnail'):
                        embed.set_thumbnail(url=track_info['thumbnail'])
                    embed.add_field(name="Duration", value=str(timedelta(seconds=track_info['duration'])))
                    embed.add_field(name="Platform", value=platform.title())
                    embed.add_field(name="Requested by", value=ctx.author.mention)
                    await ctx.send(embed=embed)

            except Exception as e:
                await ctx.send(f"An error occurred: {str(e)}")

    @commands.command()
    async def skip(self, ctx):
        """Skips the current track"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Skipped current track")
        else:
            await ctx.send("Nothing is playing right now!")

    @commands.command()
    async def queue(self, ctx):
        """Shows the current queue"""
        if ctx.guild.id not in self.queue or not self.queue[ctx.guild.id]:
            await ctx.send("Queue is empty!")
            return

        embed = discord.Embed(
            title="Current Queue",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )

        if ctx.guild.id in self.now_playing:
            current = self.now_playing[ctx.guild.id]
            embed.add_field(
                name="Now Playing",
                value=f"[{current['title']}]({current['webpage_url']})\nRequested by: {current['requester'].mention}",
                inline=False
            )

        queue_list = ""
        for i, track in enumerate(self.queue[ctx.guild.id], 1):
            duration = str(timedelta(seconds=track['duration']))
            queue_list += f"`{i}.` [{track['title']}]({track['webpage_url']}) | `{duration}` | {track['requester'].mention}\n"

        if queue_list:
            embed.add_field(name="Up Next", value=queue_list, inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def clearqueue(self, ctx):
        """Clears the queue"""
        if ctx.guild.id in self.queue:
            self.queue[ctx.guild.id].clear()
            await ctx.send("🗑️ Queue cleared!")
        else:
            await ctx.send("Queue is already empty!")


    @commands.command()
    async def volume(self, ctx, volume: int):
        """Adjusts the player volume (0-100)"""
        if not ctx.voice_client:
            await ctx.send("Not connected to a voice channel!")
            return
            
        if 0 <= volume <= 100:
            ctx.voice_client.source.volume = volume / 100
            await ctx.send(f"Volume set to {volume}%")
        else:
            await ctx.send("Volume must be between 0 and 100")

    @commands.command()
    async def loop(self, ctx, mode: str = None):
        """Sets loop mode (off/song/queue)"""
        if mode not in [None, 'off', 'song', 'queue']:
            await ctx.send("Valid loop modes: off, song, queue")
            return
            
        self.loop_mode[ctx.guild.id] = None if mode in [None, 'off'] else mode
        await ctx.send(f"Loop mode set to: {mode or 'off'}")

    @commands.command()
    async def shuffle(self, ctx):
        """Shuffles the current queue"""
        if not self.queue.get(ctx.guild.id):
            await ctx.send("Queue is empty!")
            return
            
        random.shuffle(self.queue[ctx.guild.id])
        await ctx.send("🔀 Queue shuffled!")

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Playback stopped and disconnected")

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current track"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("Playback paused")

    @commands.command()
    async def resume(self, ctx):
        """Resumes the current track"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("Playback resumed")

async def setup(bot):
    await bot.add_cog(Music(bot))
