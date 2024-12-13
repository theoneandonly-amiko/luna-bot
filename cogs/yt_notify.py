import discord
from discord.ext import commands, tasks
import os
import json
import aiohttp
import asyncio
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from googleapiclient import errors
import logging

logger = logging.getLogger(__name__)

class YouTubeNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings_file = 'cogs/data/youtube_settings.json'
        self.settings = self.load_settings()
        self.youtube = build('youtube', 'v3', developerKey=self.bot.TRACKING_YT_APIKEY)
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.default_fetch_limit = 5
        self.default_timezone = timezone.utc
        self.check_uploads.start()
    
    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                # Initialize processed_videos for existing channels
                for guild_settings in settings.values():
                    if 'tracked_channels' in guild_settings:
                        for channel_data in guild_settings['tracked_channels'].values():
                            if 'processed_videos' not in channel_data:
                                channel_data['processed_videos'] = []
                return settings
        return {}
    
    def save_settings(self):
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)

    async def batch_channel_check(self, channel_ids, parts='snippet'):
        """Batch check multiple channels at once"""
        return self.youtube.channels().list(
            part=parts,
            id=','.join(channel_ids),
            maxResults=50
        ).execute()

    def should_check_now(self, channel_data):
        """Determine if channel should be checked based on historical upload patterns"""
        current_hour = datetime.now().hour
        active_hours = channel_data.get('active_hours', range(24))
        return current_hour in active_hours

    async def process_channel_batch(self, channel_ids):
        retry_count = 0
        max_retries = 3
        base_delay = 1
        
        while retry_count < max_retries:
            try:
                videos_response = await self.batch_channel_check(channel_ids)
                # Process videos
                return videos_response
            except errors.HttpError as e:
                if e.resp.status == 403 and 'quotaExceeded' in str(e):
                    await self.notify_quota_exceeded(e)
                    return
                retry_count += 1
                await asyncio.sleep(base_delay * (2 ** retry_count))

    async def notify_quota_exceeded(self, error_details):
        """Handle quota exceeded with tracking and auto-pause"""
        # Store the quota exceeded timestamp
        self.last_quota_exceeded = datetime.now(timezone.utc)
        
        # Pause the check_uploads task
        self.check_uploads.cancel()
        
        owner = await self.bot.fetch_user(self.bot.DEV_USER_ID)
        if owner:
            embed = discord.Embed(
                title="⚠️ YouTube API Quota Alert",
                description="YouTube tracking system automatically paused.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Error Details", value=str(error_details))
            embed.add_field(name="Auto Recovery", value="System will resume at midnight PT (YouTube quota reset)")
            embed.add_field(name="Manual Override", value="Use `refreshtracking` to force restart tracking")
            await owner.send(embed=embed)
            
            # Schedule auto-restart at quota reset (midnight PT)
            await self.schedule_tracking_restart()

    async def schedule_tracking_restart(self):
        """Schedule tracking restart at quota reset time"""
        utc_tz = timezone.utc
        now = datetime.now(utc_tz)
        tomorrow = now + timedelta(days=1)
        midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        wait_seconds = (midnight - now).total_seconds()
    
        await asyncio.sleep(wait_seconds)
        self.check_uploads.start()


    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def notifychannel(self, ctx, channel: discord.TextChannel):
        """Set the notification channel for YouTube updates"""
        guild_id = str(ctx.guild.id)
        if guild_id not in self.settings:
            self.settings[guild_id] = {}
    
        self.settings[guild_id]['notify_channel'] = channel.id
        self.save_settings()
    
        embed = discord.Embed(
            title="YouTube Notifications Channel Set",
            description=f"Notifications will be sent to {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def trackchannel(self, ctx, channel_input: str, track_count: int = 5, tz: str = "UTC"):
        """Track a YouTube channel and send updates to the notification channel"""
        try:
            if not 1 <= track_count <= 10:
                await ctx.send("Track count must be between 1 and 10 videos.")
                return

            # Extract channel ID from input
            if 'youtube.com/channel/' in channel_input:
                channel_id = channel_input.split('youtube.com/channel/')[-1].split('/')[0]
            else:
                channel_id = channel_input  # Use input directly as channel ID

            channel_response = self.youtube.channels().list(
                part='snippet',
                id=channel_id
            ).execute()

            if not channel_response['items']:
                await ctx.send("Channel not found! Make sure you provided a valid channel ID or URL.")
                return

            channel_info = channel_response['items'][0]['snippet']
            guild_id = str(ctx.guild.id)

            if guild_id not in self.settings:
                self.settings[guild_id] = {'tracked_channels': {}}
        
            if 'tracked_channels' not in self.settings[guild_id]:
                self.settings[guild_id]['tracked_channels'] = {}

            self.settings[guild_id]['tracked_channels'][channel_id] = {
                'name': channel_info['title'],
                'last_video_id': None,
                'track_count': track_count,
                'processed_videos': [],
                'custom_message': "🎉 **{channel_name}** just uploaded a new video!\n{video_url}",
                'timezone': tz  # Add timezone setting
            }
        
            self.save_settings()

            embed = discord.Embed(
                title="YouTube Channel Tracked",
                description=f"Now tracking: {channel_info['title']}\nTrack count set to: {track_count} videos",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"Error tracking channel: {e}")
            await ctx.send("An error occurred while trying to track the channel.")
            
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setchanneltz(self, ctx, channel_input: str, tz: str):
        try:
            timezone(timedelta(hours=int(tz)))
        except ValueError:
            await ctx.send("Invalid timezone. Please use hours offset like '7' or '-8'")
            return
        guild_id = str(ctx.guild.id)
        channel_id = channel_input.split('youtube.com/channel/')[-1].split('/')[0] if 'youtube.com/channel/' in channel_input else channel_input
        
        if guild_id in self.settings and 'tracked_channels' in self.settings[guild_id] and channel_id in self.settings[guild_id]['tracked_channels']:
            self.settings[guild_id]['tracked_channels'][channel_id]['timezone'] = tz
            self.save_settings()
            await ctx.send(f"Timezone for {self.settings[guild_id]['tracked_channels'][channel_id]['name']} set to {tz}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def settrackcount(self, ctx, channel_input: str, count: int):
        """Set how many new videos to track for a specific YouTube channel (1-10)"""
        if not 1 <= count <= 10:
            await ctx.send("Track count must be between 1 and 10 videos.")
            return

        guild_id = str(ctx.guild.id)
        channel_id = channel_input.split('youtube.com/channel/')[-1].split('/')[0] if 'youtube.com/channel/' in channel_input else channel_input

        if guild_id not in self.settings or 'tracked_channels' not in self.settings[guild_id] or \
           channel_id not in self.settings[guild_id]['tracked_channels']:
            await ctx.send("This channel is not being tracked!")
            return

        self.settings[guild_id]['tracked_channels'][channel_id]['track_count'] = count
        self.save_settings()

        channel_name = self.settings[guild_id]['tracked_channels'][channel_id]['name']
        embed = discord.Embed(
            title="Track Count Updated",
            description=f"Now tracking {count} most recent videos for {channel_name}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def confignotimessage(self, ctx, channel_input: str):
        """Configure notification message for a tracked YouTube channel"""
        guild_id = str(ctx.guild.id)
        channel_id = channel_input.split('youtube.com/channel/')[-1].split('/')[0] if 'youtube.com/channel/' in channel_input else channel_input

        if guild_id not in self.settings or 'tracked_channels' not in self.settings[guild_id] or \
           channel_id not in self.settings[guild_id]['tracked_channels']:
            await ctx.send("This channel is not being tracked!")
            return

        embed = discord.Embed(
            title="Notification Message Configuration",
            description="Please enter your custom notification message.\n\nAvailable variables:\n"
                       "`{channel_name}` - YouTube channel name\n"
                       "`{video_title}` - Video title\n"
                       "`{video_url}` - Video URL\n"
                       "`{video_description}` - Video description",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

        try:
            msg = await self.bot.wait_for(
                'message',
                timeout=60.0,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )

            self.settings[guild_id]['tracked_channels'][channel_id]['custom_message'] = msg.content
            self.save_settings()

            await ctx.send("✅ Notification message updated successfully!")

        except asyncio.TimeoutError:
            await ctx.send("Configuration timed out. Please try again.")

    @commands.command()
    @commands.is_owner()
    async def refreshtracking(self, ctx):
        """[Owner] Force refresh YouTube tracking"""
        embed = discord.Embed(
            title="YouTube Tracking Refresh",
            description="Manually checking for new uploads...",
            color=discord.Color.blue()
        )
        status_msg = await ctx.send(embed=embed)
    
        await self.check_uploads()
    
        embed.description = "Tracking refresh completed!"
        embed.color = discord.Color.green()
        await status_msg.edit(embed=embed)
    
    @tasks.loop(hours=24)
    async def check_uploads(self):
        try:
            channel_batch = []
            
            for guild_id, guild_settings in self.settings.items():
                if 'tracked_channels' not in guild_settings:
                    continue
                    
                for channel_id, channel_data in guild_settings['tracked_channels'].items():
                    # Get channel's timezone
                    channel_tz = timezone(timedelta(hours=int(channel_data.get('timezone', 0))))
                    channel_time = datetime.now(channel_tz)
                    
                    # Check if it's the right time in channel's timezone
                    if channel_time.hour == 0 and channel_time.minute < 15:  # Within first 15 mins of day
                        channel_batch.append(channel_id)
                        
                        if len(channel_batch) >= 50:
                            await self.process_channel_batch(channel_batch)
                            channel_batch = []
                            await asyncio.sleep(1)
            
            if channel_batch:
                await self.process_channel_batch(channel_batch)
                
        except errors.HttpError as e:
            if e.resp.status == 403 and 'quotaExceeded' in str(e):
                await self.notify_quota_exceeded(e)    

    @check_uploads.before_loop
    async def before_check_uploads(self):
        await self.bot.wait_until_ready()
        
        # Set target time (e.g. 00:00 UTC)
        now = datetime.now(timezone.utc)
        target_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # If we're past target time today, schedule for tomorrow
        if now > target_time:
            target_time += timedelta(days=1)
            
        # Wait until next target time
        await asyncio.sleep((target_time - now).total_seconds())


async def setup(bot):
    await bot.add_cog(YouTubeNotifier(bot))
