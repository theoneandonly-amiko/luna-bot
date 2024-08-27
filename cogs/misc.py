import discord
from discord.ext import commands


from discord.ext.commands import BucketType

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='usercount', help='Let you know how many members are in the current server.')
    @commands.cooldown(1, 60, BucketType.user)  # 1 use per 60 seconds per user
    async def usercount(self, ctx):
        guild = ctx.guild  # Get the server (guild) the command was issued in
        member_count = guild.member_count  # Get the number of members in the server
        await ctx.send(f'This server has {member_count} members!')

    @usercount.error
    async def usercount_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'Too fast. Please try again after {int(error.retry_after)} seconds.')

    @commands.command(name='ping')
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        ping_message = f"Pong! Latency: {latency}ms"

        await ctx.send(ping_message)

async def setup(bot):
    await bot.add_cog(Misc(bot))
