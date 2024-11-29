import time
from datetime import datetime, timezone

import discord
from discord.ext import commands
from discord.ext.commands import BucketType

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.command_invokes = 0

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.command_invokes += 1

    @commands.command(name="stats", help="Displays bot statistics.")
    @commands.cooldown(1, 10, BucketType.user)  # 1 use per 10 seconds per user
    async def stats(self, ctx):
        # Calculate uptime
        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Get the number of guilds (servers) and users
        guild_count = len(self.bot.guilds)
        user_count = len(self.bot.users)  # More efficient

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

    @commands.command(name='membercount', help='Shows the number of members in the current server.')
    @commands.cooldown(1, 60, BucketType.user)  # 1 use per 60 seconds per user
    async def membercount(self, ctx):
        guild = ctx.guild  # Get the server (guild) the command was issued in
        member_count = guild.member_count  # Get the number of members in the server
        await ctx.send(f'This server has {member_count} members!')

    @commands.command(name='ping', help='Displays the bot latency.')
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(title='Pong!', description=f'Bot latency: {latency}ms', color=discord.Color.blue())

        await ctx.send(embed=embed)

    @commands.command(name='msg', help='Sends a message to a specified channel.')
    @commands.is_owner()  # Only the bot owner can use this command
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

    @commands.command(name='whois', help='Displays information about a user.')
    async def whois(self, ctx, member: discord.Member = None):
        """Displays information about the mentioned user."""
        member = member or ctx.author  # Default to the command invoker if no member is mentioned

        # User information
        registered_date = member.created_at.strftime("%a, %b %d, %Y %I:%M %p")  # Custom format
        joined_date = member.joined_at.strftime("%a, %b %d, %Y %I:%M %p")  # Custom format

        # Get roles, excluding @everyone
        roles = [role for role in member.roles if role != ctx.guild.default_role]

        # Key permissions mapping
        key_permissions = [
            ('administrator', 'Administrator'),
            ('manage_guild', 'Manage Server'),
            ('manage_roles', 'Manage Roles'),
            ('manage_channels', 'Manage Channels'),
            ('manage_messages', 'Manage Messages'),
            ('manage_webhooks', 'Manage Webhooks'),
            ('manage_nicknames', 'Manage Nicknames'),
            ('manage_emojis_and_stickers', 'Manage Emojis and Stickers'),
            ('kick_members', 'Kick Members'),
            ('ban_members', 'Ban Members'),
            ('mention_everyone', 'Mention Everyone'),
        ]

        # Check which permissions the member has
        permissions = [name for perm, name in key_permissions if getattr(member.guild_permissions, perm)]

        # Acknowledgment part
        acknowledgment = None
        if ctx.guild.owner_id == member.id:
            acknowledgment = "This user is the **Server Owner**."
        elif member.guild_permissions.administrator:
            acknowledgment = "This user is an **Administrator**."
        elif any(getattr(member.guild_permissions, perm) for perm, _ in key_permissions[1:]):
            acknowledgment = "This user is a **Staff/Moderator**."

        # Create embed
        embed = discord.Embed(title=f"About User: {member}", color=discord.Color.blue())
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.add_field(name="Account Created On", value=registered_date)
        embed.add_field(name="Joined Server On", value=joined_date)

        # Mention roles
        mentioned_roles = ', '.join(role.mention for role in roles) if roles else "No Roles"
        embed.add_field(name="Roles", value=mentioned_roles, inline=False)

        embed.add_field(
            name="Key Permissions",
            value=", ".join(permissions) if permissions else "No Key Permissions",
            inline=False
        )

        # Acknowledgment field
        if acknowledgment:
            embed.add_field(name="Acknowledgment", value=acknowledgment, inline=False)

        # Set user avatar as icon and thumbnail
        embed.set_thumbnail(url=member.display_avatar.url)  # Thumbnail for avatar

        # Set footer
        embed.set_footer(text=f"User ID: {member.id}")

        # Send the embed
        await ctx.send(embed=embed)

    @commands.command(name='info', help='Displays information about the bot.')
    async def info(self, ctx):
        embed = discord.Embed(title="About Me", color=discord.Color.brand_green())

        embed.add_field(
            name="Short Introduction",
            value=(
                "Hey there, I'm Luna, your trusty bot with humble beginnings! I was created during my owner's first coding adventure—so expect a few quirks along the way. 😅\n"
                "You might run into a few bumps when using my features—just blame it on my owner's coding oversights! But hey, learning is part of the journey, right?\n"
                "For now, I'm still in development, so think of yourselves as my elite users! Got feature ideas? Share them, and I'll make sure you get the credit! 🎉"
            ),
            inline=False
        )
        embed.add_field(
            name="Credits",
            value=(
                "**Additional Designs:**\n"
                "1. the_peacekeeper_recruitment\n"
                "2. rbcube_\n"
                "3. ganyuvngenshin\n\n"
                "**Quality Assurances:**\n"
                "1. thai2910\n"
                "2. Ahmed577"
            ),
            inline=False
        )
        embed.set_footer(text='Made by Luna Starry with ❤️.')

        await ctx.send(embed=embed)

    @commands.command(name="guildinfo", help="Shows information about the guild.")
    async def guild_info(self, ctx):
        guild = ctx.guild

        # Count different channel types
        category_count = sum(1 for channel in guild.channels if isinstance(channel, discord.CategoryChannel))
        text_channel_count = sum(1 for channel in guild.channels if isinstance(channel, discord.TextChannel))
        voice_channel_count = sum(1 for channel in guild.channels if isinstance(channel, discord.VoiceChannel))

        # Use the server's creation date
        creation_date = guild.created_at.strftime("%d/%m/%Y %I:%M %p")

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
        embed.set_footer(text=f"Guild ID: {guild.id} | Server created on {creation_date}")

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
        embed.set_image(url=member.display_avatar.url)  # Full-size avatar image
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    @commands.command(name='scanguild', help='Displays information about all guilds the bot has joined.')
    @commands.is_owner()
    async def scanguild(self, ctx):
        guilds_info = ""
        for guild in self.bot.guilds:
            guilds_info += f"**Name:** {guild.name}\n"
            guilds_info += f"**ID:** {guild.id}\n"
            guilds_info += f"**Members:** {guild.member_count}\n"
            guilds_info += f"**Text Channels:** {len(guild.text_channels)}\n"
            guilds_info += f"**Voice Channels:** {len(guild.voice_channels)}\n\n"

        # Split the message if it exceeds Discord's character limit
        for chunk in [guilds_info[i:i+2000] for i in range(0, len(guilds_info), 2000)]:
            embed = discord.Embed(description=chunk, color=discord.Color.blue())
            await ctx.send(embed=embed)

        await ctx.send(f"Total number of guilds the bot has joined: **{len(self.bot.guilds)}**")

    @commands.command(name='leaveguild', help='Forces the bot to leave a guild.')
    @commands.is_owner()
    async def leaveguild(self, ctx, guild_id: int):
        try:
            guild = self.bot.get_guild(guild_id)
            if guild:
                await guild.leave()
                embed = discord.Embed(
                    title="Guild Left",
                    description=f"I have left the guild: **{guild.name}**.",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Guild ID:", value=guild.id, inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send("I cannot find a guild with that ID.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(Misc(bot))