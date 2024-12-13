import os
import random
import logging
import discord
import logging
from datetime import datetime, timezone

from discord.ext import commands, tasks
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .constants import keyword_responses
from .utils import get_all_videos

class LunaBot(commands.Bot):

    def __init__(self, youtube_api_key, youtube_channel_id, dev_user_id, tracking_yt_apikey):
        self.YOUTUBE_API_KEY = youtube_api_key
        self.YOUTUBE_CHANNEL_ID = youtube_channel_id
        self.DEV_USER_ID = dev_user_id
        self.TRACKING_YT_APIKEY = tracking_yt_apikey

        discord.utils.setup_logging(root=True)
        self.logger = logging.getLogger()

        # Initialize the YouTube API client
        self.youtube = build('youtube', 'v3', developerKey=self.YOUTUBE_API_KEY)
        super().__init__(
            command_prefix = "&",
            intents=discord.Intents.all(),
            case_insensitive=True,
            help_command=None,
            owner_ids=[self.DEV_USER_ID, 521226389559443461] # owner ids
        )
        self.add_check(self.globally_block_dms)
        
        # Enhanced caching system
        self.video_cache = []
        self.last_cache_update = None
        self.cache_duration = 3600  # 1 hour cache
        
        # Separate update intervals
        self.youtube_update_interval = 30  # minutes
        self.status_update_interval = 10   # minutes

    async def on_ready(self):
        self.logger.info(f"{self.user} is connected and ready to use.")
        self.update_youtube_presence.start()
        self.update_custom_status.start()

        # load jiskau
        await self.load_extension("jishaku")

        # load cogs
        for filename in os.listdir("./cogs/"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")
    
    # Global check to disallow commands in DMs
    async def globally_block_dms(self, ctx):
        if ctx.guild is None:  # Check if the command is invoked in DMs
            return False  # Disallow the command
        return True  # Allow the command if it's in a guild

    # =================== Youtube Presence ====================
    @tasks.loop(minutes=30)  # YouTube presence updates every 30 mins
    async def update_youtube_presence(self):
        try:
            if await self.needs_cache_refresh():
                await self.refresh_video_cache()
                
            if self.video_cache:
                random_video = random.choice(self.video_cache)
                title = random_video.get('snippet', {}).get('title', 'Unknown Title')
                channel = random_video.get('snippet', {}).get('channelTitle', 'Unknown Channel')
                video_id = (
                    random_video.get('id', {}).get('videoId') or 
                    random_video.get('videoId') or 
                    'unknown_id'
                )
                
                video_url = f'https://www.youtube.com/watch?v={video_id}'
                await self.change_presence(activity=discord.Streaming(
                    name=f'{title} by {channel}',
                    url=video_url
                ))
        except Exception as e:
            self.logger.error(f"Error updating YouTube presence: {e}")

    @tasks.loop(minutes=5)  # Custom status updates every 5 mins
    async def update_custom_status(self):
        if not self.video_cache:
            funny_statuses = [
                "Searching for videos in the void 🕵️",
                "Cache went on vacation 🏖️",
                "YouTube.exe has stopped working 💻",
                "Buffering... forever 🔄",
                "Lost in the YouTube wilderness 🌲",
                "Debugging my video radar 🛰️",
                "Where are my videos? 🤔",
                "YouTube quota go brrr 🚫",
                "API limits said no 🛑",
                "Quota exceeded, vibing mode ON 😎",
                "YouTube playing hard to get 🙈",
                "Waiting for API credits to reload 🔄",
                "Quota drama in progress 🎭",
                "403: Forbidden Dance Party 💃",
                "Permissions? Never heard of them 🙈",
                "Sneaking past error firewalls 🕵️",
                "Error: Coolness Overload 😎",
                "Waiting for YouTube to calm down 🧘",
                "Debugging the universe 🌌",
                "Permissions are just suggestions 🤷",
                "Caught in the 403 zone 🚧",
                "YouTube is on vacation now. Brb",
            ]
            await self.change_presence(
                status=discord.Status.online,
                activity=discord.CustomActivity(name=random.choice(funny_statuses))
            )

    async def needs_cache_refresh(self):
        if not self.video_cache or not self.last_cache_update:
            return True
        now = datetime.now(timezone.utc)
        return (now - self.last_cache_update).total_seconds() > self.cache_duration

    async def refresh_video_cache(self):
        videos = get_all_videos(self.YOUTUBE_CHANNEL_ID, self.youtube)
        if videos:
            self.video_cache = videos
            self.last_cache_update = datetime.now(timezone.utc)
            self.logger.info("Video cache refreshed successfully")

    @update_youtube_presence.before_loop
    @update_custom_status.before_loop
    async def before_update_presence(self):
        await self.wait_until_ready()

    # ========================================================

    # Event handler for when a command is invoked
    async def on_command(self, ctx):
        guild = ctx.guild
        channel = ctx.channel
        author = ctx.author
        command = ctx.command

        if guild is None:
            # Handle DM scenario, where there's no guild
            self.logger.info(f"Command '{command}' invoked by {author} in DM on channel '{channel}'. Action prevented.")
        else:
            # Handle command invoked in a guild (server)
            self.logger.info(f"Command '{command}' invoked by {author} in guild \"{guild}\" on channel '{channel}'.")



    # Handle and log command errors with custom messages
    async def on_command_error(self, ctx, error):
        embed = discord.Embed(title="Error", color=discord.Color.red())

        # Handle the case where a command is prevented due to DM check
        if isinstance(error, commands.CheckFailure):
            return  # Ignore this error silently

        # Handle 'CommandNotFound' error
        if isinstance(error, commands.CommandNotFound):
            embed.description = "Sorry, I couldn't find that command. Please check the command and try again."
            await ctx.send(embed=embed)

        # Handle 'CommandOnCooldown' error
        elif isinstance(error, commands.CommandOnCooldown):
            embed.description = f"This command is on cooldown. Please try again in {int(error.retry_after)} seconds."
            await ctx.send(embed=embed)

        # Log other errors generically without sending a message
        else:
            self.logger.error(f"Error with command '{ctx.command}': {error}")
    

    async def on_message(self, message):
        if message.author.bot:
            return  # Ignore messages sent by the bot itself
    
        # Check for keywords and send appropriate responses with username
        for keyword, responses in keyword_responses.items():
            if keyword in message.content.lower():
                response = random.choice(responses)
                await message.channel.send(f'{response}')
                break  # Exit loop after sending a response
        await self.process_commands(message)  # "Again, please don't stop working", Amiko said.