import discord
from discord.ext.commands import BucketType
from discord.ext import commands
import time
from datetime import datetime

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

        # Create an embed message for bot stats
        embed = discord.Embed(title="Bot Statistics", color=discord.Color.blue())
        embed.add_field(name="Servers", value=str(guild_count), inline=True)
        embed.add_field(name="Users", value=str(user_count), inline=True)
        embed.add_field(name="Uptime", value=f"{hours}h {minutes}m {seconds}s", inline=True)
        embed.add_field(name="Latency", value=f"{latency}ms", inline=True)
        embed.add_field(name="Commands Invoked", value=str(self.command_invokes), inline=True)

        # Send the embed message
        await ctx.send(embed=embed)

    @commands.command(name='totaluser', help='Let you know how many members are in the current server.')
    @commands.cooldown(1, 60, BucketType.user)  # 1 use per 60 seconds per user
    async def totaluser(self, ctx):
        guild = ctx.guild  # Get the server (guild) the command was issued in
        member_count = guild.member_count  # Get the number of members in the server
        await ctx.send(f'This server has {member_count} members!')

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



    @commands.command(name='whois')
    async def whois(self, ctx, member: discord.Member):
        """Displays information about the mentioned user."""
        # User information
        registered_date = member.created_at.strftime("%a, %b %d, %Y %I:%M %p")  # Custom format
        joined_date = member.joined_at.strftime("%a, %b %d, %Y %I:%M %p")  # Custom format
        
        # Get roles, ensuring we keep discord.Role objects
        roles = [role for role in member.roles if role.name != "@everyone"]
        
        key_permissions = [
            'administrator', 
            'manage_guild', 
            'manage_roles', 
            'manage_channels', 
            'manage_messages', 
            'manage_webhooks', 
            'manage_nicknames', 
            'manage_emojis_and_stickers', 
            'kick_members', 
            'ban_members', 
            'mention_everyone', 
        ]
        
        # Get key permissions with user-friendly names
        permissions = []
        for perm in key_permissions:
            try:
                if getattr(member.guild_permissions, perm):
                    permissions.append(perm.replace('_', ' ').capitalize())
            except AttributeError:
                continue
        
        # Acknowledgment part
        acknowledgment = ""
        if ctx.guild.owner_id == member.id:
            acknowledgment = "This user is the **Server Owner**."
        elif member.guild_permissions.administrator:
            acknowledgment = "This user is an **Administrator**."
        elif member.guild_permissions.manage_guild or member.guild_permissions.manage_roles:
            acknowledgment = "This user is a **Staff/Moderator**."

        # Create embed
        embed = discord.Embed(title=f"About user: {member}", color=discord.Color.blue())
        embed.set_author(name=str(member), icon_url=member.avatar.url)
        embed.add_field(name="Account Created On", value=registered_date)
        embed.add_field(name="Joined Server On", value=joined_date)
        
        # Mention roles
        mentioned_roles = ', '.join(role.mention for role in roles) if roles else "No Roles"
        embed.add_field(name="Roles", value=mentioned_roles, inline=False)
        embed.add_field(name="Key Permissions", value=", ".join(permissions) if permissions else "No Key Permissions", inline=False)
        # Acknowledgment field
        if acknowledgment:
            embed.add_field(name="Acknowledgment", value=acknowledgment, inline=False)
        # Set user avatar as icon and thumbnail
        embed.set_thumbnail(url=member.avatar.url)  # Thumbnail for avatar        
        # Set footer
        embed.set_footer(text=f"User ID: {member.id}")

        # Send the embed
        await ctx.send(embed=embed)

    @commands.command(name='info')
    async def info(self, ctx):
        embed = discord.Embed(title="About me", color=discord.Color.brand_green())
        embed.add_field(name="Short introduction", value= 
            "Hey there, I'm Amiker, your trusty bot with humble beginnings! I was created during my owner's first coding adventure—so expect a few quirks along the way. 😅\n"
            "You might run into a few bumps when using my features—just blame it on my owner's coding oversights! But hey, learning is part of the journey, right?\n"
            "For now, I'm still in development, so think of yourselves as my elite beta testers! Got feature ideas? Share them, and I'll make sure you get the credit! 🎉", inline=False)

        embed.set_footer(text='Made by Lunatico with ❤️.')
        
        credit = discord.Embed(title="Credits", color=discord.Color.blurple())
        credit.add_field(name='Additional Designs', value=
            "1. the_peacekeeper_recruitment\n"
            "2. rbcube_\n"
            "3. ganyuvngenshin")
        credit.add_field(name="Quality Assurances", value=
            "1. thai2910\n"
            "2. Ahmed577")

        await ctx.send(embed=embed)
        await ctx.send(embed=credit)
        

    @commands.command(name="guildinfo", help="Shows information about the guild.")
    async def guild_info(self, ctx):
        guild = ctx.guild
        
        # Count different channel types
        category_count = sum(1 for channel in guild.channels if isinstance(channel, discord.CategoryChannel))
        text_channel_count = sum(1 for channel in guild.channels if isinstance(channel, discord.TextChannel))
        voice_channel_count = sum(1 for channel in guild.channels if isinstance(channel, discord.VoiceChannel))
        
        # Current datetime for footer
        current_time = datetime.now().strftime("%d/%m/%Y %I:%M %p")

        # Embed for guild information
        embed = discord.Embed(
            title=f"Guild Information - {guild.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Owner", value=guild.owner)
        embed.add_field(name="Member Count", value=guild.member_count)
        embed.add_field(name="Total Roles", value=len(guild.roles))
        embed.add_field(name="Category channels", value=category_count)
        embed.add_field(name="Text channels", value=text_channel_count)
        embed.add_field(name="Voice channels", value=voice_channel_count)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.set_footer(text=f"Guild ID: {guild.id} | Server created {current_time}")

        await ctx.send(embed=embed)

    @commands.command(name="avatar", help="Fetches and displays your avatar or the avatar of the mentioned user.")
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author  # Defaults to the command invoker if no member is mentioned
        
        # Display username and server nickname
        username = f"{member.name}"
        nickname = member.display_name if member.display_name != member.name else "No Server Nickname"

        embed = discord.Embed(
            title=f"{username}",
            description=f"**Server Nickname:** {nickname}",
            color=discord.Color.green()
        )
        embed.set_image(url=member.avatar.url)  # Full-size avatar image
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name='scanguild')
    @commands.is_owner()  # Restrict to owner only
    async def scanguild(self, ctx):
        guild_count = len(self.bot.guilds)  # Count the number of joined guilds
        for guild in self.bot.guilds:
            # Create an embed for each guild
            embed = discord.Embed(title="Guild Information", color=discord.Color.blue())
            embed.add_field(name="**Name:**", value=guild.name)
            embed.add_field(name="**ID:**", value=guild.id)
            embed.add_field(name="**Members:**", value=guild.member_count)
            embed.add_field(name="**Text Channels:**", value=len(guild.text_channels))
            embed.add_field(name="**Voice Channels:**", value=len(guild.voice_channels))

                # Send the embed for the current guild
            await ctx.send(embed=embed)
        await ctx.send(f"Total number of guilds the bot has joined: **{guild_count}**")

    @commands.command(name='leaveguild')
    @commands.is_owner()
    async def leaveguild(self, ctx, guild_id: int):
        # Attempt to fetch the guild using the provided ID
        guild = self.bot.get_guild(guild_id)

        # Create an embed for the response
        embed = discord.Embed(color=discord.Color.blue())

        if guild is not None:
            # Leave the guild
            await guild.leave()
            embed.title = "Guild Left"
            embed.description = f"I have left the guild: **{guild.name}**."
            embed.add_field(name="Guild ID:", value=guild.id, inline=False)
        else:
            embed.title = "Error"
            embed.description = "I cannot find a guild with that ID."

        # Send the embed response
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Misc(bot))
