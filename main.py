import os
from dotenv import load_dotenv
from core import LunaBot

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID')
DEV_USER_ID = int(os.getenv('DEV_USER_ID'))

lunaBot = LunaBot(YOUTUBE_API_KEY, YOUTUBE_CHANNEL_ID, DEV_USER_ID)
 # ================= CHECK BLACKLIST =======================
@lunaBot.check
async def check_blacklist(ctx) -> bool:
    if ctx.author.id in lunaBot.blacklisted_users:
        await ctx.reply("You are currently blacklisted and cannot use this command.")
        return False
    return True

if __name__ == "__main__":
    lunaBot.run(token, log_handler=None)