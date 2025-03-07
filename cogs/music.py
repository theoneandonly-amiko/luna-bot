import discord
import os
from discord.ext import commands
import yt_dlp
import requests
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
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
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

        cookies_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
        self.ytdlp_opts = YTDLP_OPTIONS.copy()
        self.ytdlp_opts['cookiefile'] = cookies_path
        
        self.ytdlp = yt_dlp.YoutubeDL(self.ytdlp_opts)
        self.loop_mode = {}  # None, 'song', 'queue'

    async def play_next(self, ctx):
        try:
            if not ctx.voice_client:
                return
                
            if ctx.guild.id in self.loop_mode and ctx.guild.id in self.now_playing:
                current_track = self.now_playing[ctx.guild.id]
                
                # Song loop - keep playing the same track
                if self.loop_mode[ctx.guild.id] == 'song':
                    # Use nightcore options if it's a nightcore track
                    ffmpeg_opts = {
                        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
                        'options': '-vn -filter:a "asetrate=44100*1.25,aresample=44100,atempo=1.0" -bufsize 64k'
                    } if current_track.get('is_nightcore') else FFMPEG_OPTIONS
                    source = discord.FFmpegPCMAudio(current_track['url'], **ffmpeg_opts)
                    ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
                    return
                    
                # Queue loop - add current track to end of queue
                elif self.loop_mode[ctx.guild.id] == 'queue':
                    self.queue[ctx.guild.id].append(current_track)

            if ctx.guild.id in self.queue and self.queue[ctx.guild.id]:
                next_track = self.queue[ctx.guild.id].pop(0)
                # Use nightcore options if it's a nightcore track
                ffmpeg_opts = {
                    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
                    'options': '-vn -filter:a "asetrate=44100*1.25,aresample=44100,atempo=1.0" -bufsize 64k'
                } if next_track.get('is_nightcore') else FFMPEG_OPTIONS
                source = discord.FFmpegPCMAudio(next_track['url'], **ffmpeg_opts)
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
    async def nightcore(self, ctx, platform: str, *, query):
        """Plays audio with nightcore effect (faster and higher pitch) from selected platform"""
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

        # Create nightcore FFMPEG options
        nightcore_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
            'options': '-vn -filter:a "asetrate=44100*1.25,aresample=44100" -bufsize 64k'
        }

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
                    'requester': ctx.author,
                    'is_nightcore': True
                }

                if ctx.voice_client.is_playing():
                    if ctx.guild.id not in self.queue:
                        self.queue[ctx.guild.id] = []
                    self.queue[ctx.guild.id].append(track_info)
                    
                    embed = discord.Embed(
                        title="Added to Queue (Nightcore)",
                        description=f"[{track_info['title']}]({track_info['webpage_url']})",
                        color=discord.Color.blue(),
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed.add_field(name="Position", value=str(len(self.queue[ctx.guild.id])))
                else:
                    source = discord.FFmpegPCMAudio(track_info['url'], **nightcore_options)
                    ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
                    self.now_playing[ctx.guild.id] = track_info
                    
                    embed = discord.Embed(
                        title="Now Playing (Nightcore)",
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
        """Shows the current queue with detailed information"""
        if (ctx.guild.id not in self.queue or not self.queue[ctx.guild.id]) and ctx.guild.id not in self.now_playing:
            await ctx.send("Nothing is playing and queue is empty!")
            return

        embed = discord.Embed(
            title="Music Queue",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )

        # Show loop status if active
        if ctx.guild.id in self.loop_mode and self.loop_mode[ctx.guild.id]:
            embed.set_footer(text=f"🔁 Loop Mode: {self.loop_mode[ctx.guild.id].title()}")

        # Now Playing section
        if ctx.guild.id in self.now_playing:
            current = self.now_playing[ctx.guild.id]
            duration = str(timedelta(seconds=current['duration']))
            mode_indicator = "Nightcore" if current.get('is_nightcore') else "Normal"
            
            now_playing = (
                f"[{current['title']}]({current['webpage_url']})\n"
                f"└─ {mode_indicator} | `{duration}` | {current['platform'].title()} | {current['requester'].mention}"
            )
            embed.add_field(
                name="🎶 Now Playing",
                value=now_playing,
                inline=False
            )

        # Queue section
        if self.queue[ctx.guild.id]:
            queue_list = []
            total_duration = 0
            
            for i, track in enumerate(self.queue[ctx.guild.id], 1):
                duration = str(timedelta(seconds=track['duration']))
                total_duration += track['duration']
                mode_indicator = "Nightcore" if track.get('is_nightcore') else "Normal"
                
                queue_list.append(
                    f"`{i}.` {mode_indicator} [{track['title']}]({track['webpage_url']})\n"
                    f"└─ `{duration}` | {track['platform'].title()} | {track['requester'].mention}"
                )

            # Split into pages if queue is too long
            page_size = 10
            pages = [queue_list[i:i + page_size] for i in range(0, len(queue_list), page_size)]
            
            if len(pages) > 1:
                page_info = f"\nPage 1/{len(pages)}"
            else:
                page_info = ""

            # Queue statistics
            stats = (
                f"**Total tracks:** {len(self.queue[ctx.guild.id])}\n"
                f"**Total duration:** `{str(timedelta(seconds=total_duration))}`"
                f"{page_info}"
            )
            
            embed.add_field(
                name="📑 Queue",
                value="\n".join(pages[0]),
                inline=False
            )
            embed.add_field(
                name="📊 Queue Stats",
                value=stats,
                inline=False
            )
        else:
            embed.add_field(
                name="📑 Queue",
                value="No tracks in queue",
                inline=False
            )

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
            
    @commands.command()
    async def remove(self, ctx, position: int):
        """Removes a song from the specified position in the queue"""
        if ctx.guild.id not in self.queue or not self.queue[ctx.guild.id]:
            await ctx.send("Queue is empty!")
            return
            
        if position < 1 or position > len(self.queue[ctx.guild.id]):
            await ctx.send(f"Please provide a valid position between 1 and {len(self.queue[ctx.guild.id])}!")
            return
            
        removed_track = self.queue[ctx.guild.id].pop(position - 1)
        
        embed = discord.Embed(
            title="Removed from Queue",
            description=f"[{removed_track['title']}]({removed_track['webpage_url']})",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        if removed_track.get('thumbnail'):
            embed.set_thumbnail(url=removed_track['thumbnail'])
        embed.add_field(name="Duration", value=str(timedelta(seconds=removed_track['duration'])))
        embed.add_field(name="Requested by", value=removed_track['requester'].mention)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))
