# misc.py

import discord
from discord.ext.commands import BucketType
from discord.ext import commands
import time

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.command_invokes = 0

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.command_invokes += 1

    @commands.command(name="stats", help="Displays bot statistics.")
    async def stats(self, ctx):
        # Calculate uptime
        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Get the number of guilds (servers) and users
        guild_count = len(self.bot.guilds)
        user_count = len(set(self.bot.get_all_members()))

        # Get latency (ping)
        latency = round(self.bot.latency * 1000)  # in milliseconds

        # Build the stats message
        stats_message = (
            f"**Bot Statistics**\n"
            f"Servers: {guild_count}\n"
            f"Users: {user_count}\n"
            f"Uptime: {hours}h {minutes}m {seconds}s\n"
            f"Latency: {latency}ms\n"
            f"Commands Invoked: {self.command_invokes}"
        )

        await ctx.send(stats_message)

    @commands.command(name='totaluser', help='Let you know how many members are in the current server.')
    @commands.cooldown(1, 60, BucketType.user)  # 1 use per 60 seconds per user
    async def totaluser(self, ctx):
        guild = ctx.guild  # Get the server (guild) the command was issued in
        member_count = guild.member_count  # Get the number of members in the server
        await ctx.send(f'This server has {member_count} members!')

    @totaluser.error
    async def usercount_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'Too fast. Please try again after {int(error.retry_after)} seconds.')

    @commands.command(name='ping')
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(title='Pong!', description=f'Bot latency: {latency}ms', color=discord.Color.blue())

        await ctx.send(embed=embed)
    
    @commands.command(name='msg')
    async def msg(self, ctx, channel_id: int, *, content: str):
        try:
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                await ctx.send("Channel not found!")
                return
            await channel.send(content)
            await ctx.send(f"Message sent to <#{channel_id}>")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
    @commands.command(name='info')
    async def info(self, ctx):
        embed = discord.Embed(title="About me", color=discord.Color.brand_green())
        embed.add_field(name="Short description", value=
            "I'm Amiker, the bot served with most basic purposed. I was built during the first coding journey of owner, ehehe.\n"
            "You may see some errors when using some function of me, because of some oversights that my owner made. Well, programming is fun, at least it is what it is. *sigh*... 🙄\n"
            "In the future I will be widely used, for now I'm under development, so you all are the best testers ever. Suggest features for a broad credit. Yee.", inline=False)
        embed.set_footer(text='"Big W in programming, ehe. - Lunatico"')
        
        credit = discord.Embed(title="Credits", color=discord.Color.blurple())
        credit.add_field(name='Additional Designs', value=
            "1. the_peacekeeper_recruitment (ErrorBonnieTPkR)")
        
        await ctx.send(embed=embed)
        await ctx.send(embed=credit)
async def setup(bot):
    await bot.add_cog(Misc(bot))
