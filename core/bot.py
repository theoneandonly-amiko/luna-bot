import os
import random
import logging
import discord
import logging

from discord.ext import commands, tasks
from googleapiclient.discovery import build

from .constants import keyword_responses
from .utils import get_all_videos

class LunaBot(commands.Bot):

    def __init__(self, youtube_api_key, youtube_channel_id, dev_user_id):
        self.YOUTUBE_API_KEY = youtube_api_key
        self.YOUTUBE_CHANNEL_ID = youtube_channel_id
        self.DEV_USER_ID = dev_user_id

        self.BLACKLIST_FILE = 'blacklist.json'
        self.blacklisted_users = set()


        # Initialize the YouTube API client
        self.youtube = build('youtube', 'v3', developerKey=self.YOUTUBE_API_KEY)
        super().__init__(
            command_prefix = "&",
            intents=discord.Intents.all(),
            case_insensitive=True,
            help_command=None,
            owner_ids=[self.DEV_USER_ID, 521226389559443461] # owner ids
        )
        


    async def on_ready(self):
        print(f"{self.user} is connected and ready to use.")
        self.update_presence.start()

        # load jiskau
        await self.load_extension("jishaku")

        # load cogs
        for filename in os.listdir("./cogs/"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")
    
   

    # =================== Youtube Presence ====================
    @tasks.loop(minutes=5)
    async def update_presence(self):
        videos = get_all_videos(self.YOUTUBE_CHANNEL_ID, self.youtube)
        if videos:  # Check if the list is not empty
            random_video = random.choice(videos)  # Choose a random video from the list
            title = random_video['snippet']['title']
            channel = random_video['snippet']['channelTitle']
            await self.change_presence(activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f'{title} by {channel}'
        ))
        else:
            logging.warning("No videos found or failed to fetch videos.")

    @update_presence.before_loop
    async def before_update_presence(self):
        await self.wait_until_ready()

    # ========================================================
    # Log all commands used
    async def on_command(self, ctx):
        command_name = ctx.command
        user = ctx.author
        guild = ctx.guild
        channel = ctx.channel
        logging.info(f"Command '{command_name}' invoked by {user} in guild '{guild}' in channel '{channel}'.")

    # Log errors
    async def on_command_error(sefl, ctx, error):
        logging.error(f"Error in command '{ctx.command}' by {ctx.author}: {error}")
    

    async def on_message(self, message):
        if message.author == self.user:
            return  # Ignore messages sent by the bot itself
    
        # Check for keywords and send appropriate responses with username
        for keyword, responses in keyword_responses.items():
            if keyword in message.content.lower():
                response = random.choice(responses)
                await message.channel.send(f'{response}')
                break  # Exit loop after sending a response
    
        await self.process_commands(message)  # "Again, please don't stop working", Amiko said.