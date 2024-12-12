import time
import sys
from datetime import datetime, timezone
from collections import defaultdict
import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import BucketType

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.command_invokes = 0
        self.received_dms = []

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


    @commands.command(name='dm', help='Sends a direct message to a specified user as the bot.')
    @commands.is_owner()  # Only the bot owner can use this command
    async def dm(self, ctx, user_input: str, *, content: str):
        try:
            # Try to convert the input to a User object
            user = await commands.UserConverter().convert(ctx, user_input)
        except commands.UserNotFound:
            try:
                # If conversion fails, try fetching the user by ID
                user_id = int(user_input)
                user = await self.bot.fetch_user(user_id)
            except (ValueError, discord.NotFound):
                await ctx.send("User not found. Please provide a valid mention or user ID.")
                return

        try:
            await user.send(content)
            await ctx.send(f"Message sent to {user.name}.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages sent by the bot itself
        if message.author.bot:
            return

        # Check if the message is a DM
        if isinstance(message.channel, discord.DMChannel):
            # Store the DM in the list
            self.received_dms.append((message.author, message.content))

            # Get the bot owner
            owner = (await self.bot.application_info()).owner
            if owner:
                # Forward the message to the bot owner
                embed = discord.Embed(
                    title="New DM Received",
                    description=message.content,
                    color=discord.Color.purple(),
                    timestamp=message.created_at
                )
                embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
                await owner.send(embed=embed)

    @commands.command(name='scandm', help='Lists all DMs received by the bot during the current session.')
    @commands.is_owner()
    async def scandm(self, ctx):
        if not self.received_dms:
            await ctx.send("No DMs received during this session.")
            return

        # Group messages by author
        messages_by_author = defaultdict(list)
        for author, content in self.received_dms:
            messages_by_author[author].append(content)

        # Create an embed for each author
        for author, messages in messages_by_author.items():
            embed = discord.Embed(
                title=f"DMs from {author}",
                description="\n".join(messages),
                color=discord.Color.blue()
            )
            embed.set_author(name=str(author), icon_url=author.display_avatar.url)
            await ctx.send(embed=embed)

    @commands.command(name='countlines')
    @commands.is_owner()  # Ensures only the bot owner can use this command
    async def count_cog_lines(self, ctx):
        """Count the number of lines in each loaded cog."""
        cog_lines = {}
        
        # Iterate through loaded cogs
        for cog_name, cog in self.bot.cogs.items():
            # Get the file path of the cog
            cog_file = sys.modules[cog.__module__].__file__
            
            try:
                with open(cog_file, 'r', encoding='utf-8') as file:
                    # Count non-empty lines, ignoring comments and blank lines
                    lines = [line.strip() for line in file if line.strip() and not line.strip().startswith('#')]
                    cog_lines[cog_name] = len(lines)
            except Exception as e:
                cog_lines[cog_name] = f"Error reading file: {e}"
        
        # Create an embed to display the results
        embed = discord.Embed(
            title="Cog Line Counts",
            color=discord.Color.blue()
        )
        
        # Add each cog's line count as a field
        for cog, line_count in sorted(cog_lines.items(), key=lambda x: x[1], reverse=True):
            embed.add_field(
                name=cog, 
                value=f"{line_count} line"
            )
        
        # Add total line count
        total_lines = sum(count for count in cog_lines.values() if isinstance(count, int))
        embed.set_footer(text=f"Total lines across all cogs: {total_lines}")
        
        await ctx.send(embed=embed)

    @commands.command(name='servericon', help='Shows the server icon in full resolution')
    async def servericon(self, ctx):
        guild = ctx.guild
        if guild.icon:
            embed = discord.Embed(
                title=f"{guild.name}'s Server Icon",
                color=discord.Color.blue()
            )
            embed.set_image(url=guild.icon.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("This server doesn't have an icon!")

    @commands.command(name='poll')
    async def poll(self, ctx, question: str = None, *options: str):
        """Create a reaction poll. Max 10 options."""
        if question is None:
            await ctx.send("Hey! To create a poll, use it like this:\n`&poll \"Your question?\" Option1 Option2 Option3`")
            return
            
        if len(options) > 10:
            await ctx.send("Maximum 10 options allowed!")
            return
        if len(options) < 2:
            await ctx.send("You need at least 2 options for a poll! Here's an example:\n`&poll \"Best color?\" Red Blue`")
            return

        # Rest of the poll command implementation stays the same
        number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        embed = discord.Embed(
            title=question,
            color=discord.Color.blue(),
            timestamp=ctx.message.created_at
        )
        
        description = []
        for idx, option in enumerate(options):
            description.append(f"{number_emojis[idx]} {option}")
        
        embed.description = "\n".join(description)
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")

        poll_msg = await ctx.send(embed=embed)
        
        for idx in range(len(options)):
            await poll_msg.add_reaction(number_emojis[idx])


    @commands.command(name='remind')
    async def remind(self, ctx, time: str, *, reminder: str):
        """Set a reminder. Example: !remind 1h30m Check the oven"""
        time_units = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }
        
        total_seconds = 0
        current_num = ''
        
        for char in time:
            if char.isdigit():
                current_num += char
            elif char.lower() in time_units:
                if current_num:
                    total_seconds += int(current_num) * time_units[char.lower()]
                    current_num = ''
                    
        if total_seconds == 0:
            await ctx.send("Invalid time format! Example: 1h30m")
            return
            
        if total_seconds > 2592000:  # 30 days
            await ctx.send("Reminder time too long! Maximum is 30 days.")
            return
            
        await ctx.send(f"I'll remind you about: {reminder} in {time}")
        
        await asyncio.sleep(total_seconds)
        
        remind_embed = discord.Embed(
            title="Reminder",
            description=reminder,
            color=discord.Color.green(),
            timestamp=ctx.message.created_at
        )
        remind_embed.set_footer(text=f"Reminder set {time} ago")
        
        await ctx.author.send(f"{ctx.author.mention}", embed=remind_embed)

    @commands.command(name='roleinfo')
    async def roleinfo(self, ctx, *, role: discord.Role):
        """Display detailed information about a role"""
        embed = discord.Embed(
            title=f"Role Information: {role.name}",
            color=role.color
        )
        
        # General info
        embed.add_field(name="Role ID", value=role.id, inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        embed.add_field(name="Position", value=role.position, inline=True)
        embed.add_field(name="Mentionable", value=role.mentionable, inline=True)
        embed.add_field(name="Hoisted", value=role.hoist, inline=True)
        embed.add_field(name="Members", value=len(role.members), inline=True)
        
        # Key permissions
        perms = []
        for perm, value in role.permissions:
            if value:
                perms.append(perm.replace('_', ' ').title())
        
        if perms:
            embed.add_field(name="Key Permissions", value="\n".join(perms), inline=False)
        
        embed.set_footer(text=f"Role Created: {role.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        await ctx.send(embed=embed)

    @commands.command(name='channelinfo')
    async def channelinfo(self, ctx, channel: discord.TextChannel = None):
        """Display information about a channel"""
        channel = channel or ctx.channel
        
        embed = discord.Embed(
            title=f"Channel Information: #{channel.name}",
            description=channel.topic or "No topic set",
            color=discord.Color.blue()
        )
        
        # General info
        embed.add_field(name="Channel ID", value=channel.id, inline=True)
        embed.add_field(name="Category", value=channel.category.name if channel.category else "None", inline=True)
        embed.add_field(name="Position", value=channel.position, inline=True)
        embed.add_field(name="NSFW", value=channel.is_nsfw(), inline=True)
        embed.add_field(name="News Channel", value=channel.is_news(), inline=True)
        embed.add_field(name="Slowmode", value=f"{channel.slowmode_delay}s" if channel.slowmode_delay else "Off", inline=True)
        
        # Channel age
        created_time = int(channel.created_at.timestamp())
        embed.add_field(name="Created At", value=f"<t:{created_time}:R>", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='firstmessage')
    async def firstmessage(self, ctx):
        """Find the first message in the current channel"""
        async for message in ctx.channel.history(limit=1, oldest_first=True):
            embed = discord.Embed(
                title="First Message",
                description=message.content,
                color=discord.Color.gold(),
                timestamp=message.created_at
            )
            embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
            embed.add_field(name="Jump to Message", value=f"[Click Here]({message.jump_url})")
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Misc(bot))