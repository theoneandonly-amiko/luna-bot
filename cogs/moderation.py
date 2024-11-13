# Made with ❤️ by Lunatico Annie. Status: Finished!

import discord
from discord.ext import commands
import json
import os
import re
import time
import datetime
from discord.ext.commands import has_permissions, MissingPermissions
from datetime import timedelta, datetime
from collections import defaultdict


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "cogs/data/automod_config.json"
        self.warnings = {}  # Initialize warnings here
        self.load_config()
        self.mute_roles_file = "cogs/data/muteroles.json"
        self.mute_roles = self.load_mute_roles()
        # Spam tracking data
        self.spam_tracker = defaultdict(list)
        self.spam_threshold = 5  # Max messages within the interval
        self.spam_interval = 10  # Time window in seconds


    def load_mute_roles(self):
        """Load existing mute roles from the JSON file."""
        try:
            with open(self.mute_roles_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_mute_roles(self):
        """Save mute roles to the JSON file."""
        with open(self.mute_roles_file, 'w') as f:
            json.dump(self.mute_roles, f, indent=4)

    def load_config(self):
        try:
            with open(self.config_file, "r") as file:
                self.config = json.load(file)
            if "word_filter" not in self.config:
                self.config["word_filter"] = []
            if "warn_threshold" not in self.config:
                self.config["warn_threshold"] = 3
            if "user_warnings" not in self.config:
                self.config["user_warnings"] = {}
        except FileNotFoundError:
            self.config = {
                "word_filter": [],
                "warn_threshold": 3,
                "user_warnings": {}
            }
        self.save_config()

    def save_config(self):
        with open(self.config_file, "w") as file:
            json.dump(self.config, file, indent=4)

    def add_warning(self, user_id: int, reason: str):
        if str(user_id) not in self.config["user_warnings"]:
            self.config["user_warnings"][str(user_id)] = []
        self.config["user_warnings"][str(user_id)].append({"reason": reason, "time": str(datetime.now())})
        self.save_config()
        return len(self.config["user_warnings"][str(user_id)]) >= self.config["warn_threshold"]

    def load_warnings(self):
        if os.path.exists(self.warnings_file):
            with open(self.warnings_file, 'r') as f:
                self.warnings = json.load(f)
        else:
            self.warnings = {}

    def save_warnings(self):
        with open(self.warnings_file, 'w') as f:
            json.dump(self.warnings, f, indent=4)

    async def punish_user(self, member, reason):
        warn_count = len(self.config["user_warnings"].get(str(member.id), []))
        if warn_count >= self.config["warn_threshold"]:
            # Check if a custom mute role is set
            mute_role = None
            if "mute_role_id" in self.config:
                mute_role = member.guild.get_role(self.config["mute_role_id"])
            
            # If no custom role, create or get the default "Muted" role
            if not mute_role:
                mute_role = discord.utils.get(member.guild.roles, name=self.config.get("mute_role_name", "Muted"))
                if not mute_role:
                    mute_role = await member.guild.create_role(name=self.config.get("mute_role_name", "Muted"))
                    for channel in member.guild.channels:
                        await channel.set_permissions(mute_role, send_messages=False, speak=False)

            await member.add_roles(mute_role)
            await member.send(f"You have been muted for repeatedly violating server rules: {reason}")

    # Kick command using User ID
    @commands.command()
    @has_permissions(kick_members=True)
    async def kick(self, ctx, user_id: int = None, *, reason=None):
        if not user_id:  # Check if user_id is provided
            embed = discord.Embed(title="Missing Required Argument", description=f"{ctx.author.mention}, please provide a valid User ID.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        user = await self.bot.fetch_user(user_id)
        member = ctx.guild.get_member(user.id)
        if member:
            try:
                await member.kick(reason=reason)
                embed = discord.Embed(title="Success", description=f'User {user} has been kicked for {reason}.', color=discord.Color.blurple())
                await ctx.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(title="Failed", description="I don't have permission to kick member. Make sure this permission has been enabled from my top role, then try again.", color=discord.Color.dark_orange())
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="User ID not found", description=f"User ID {user_id} not found in this server. Check if the User ID is valid/correct, or that member is in this server, then try again.", color=discord.Color.orange())
            await ctx.send(embed=embed)

        try:
            await user.send("You've been kicked from a guild. Consider calming yourself down or get some therapy cure. 🤷‍♀️")
        except discord.Forbidden:
            embed = discord.Embed(title="Failed", description="I cannot send a DM to this user. They might have DMs disabled.", color=discord.Color.dark_orange())

    # Ban command using User ID
    @commands.command()
    @has_permissions(ban_members=True)
    async def ban(self, ctx, user_id: int = None, *, reason=None):
        if not user_id:  # Check if user_id is provided
            embed = discord.Embed(title="Missing Required Argument", description=f"{ctx.author.mention}, please provide a valid User ID.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        user = await self.bot.fetch_user(user_id)
        await ctx.guild.ban(user, reason=reason)
        embed = discord.Embed(title="Success", description=f'User {user} has been banned for {reason}.', color=discord.Color.blurple())
        await ctx.send(embed=embed)
        # Send a notify to banned user in DM. If DM disabled by the user, notify the mods/admins.
        try:
            await user.send("You have been banned from a guild. Consider following the rules better next time.")
        except discord.Forbidden:
            embed = discord.Embed(title="Failed", description="I cannot send messages to this user. I guess they closed their DM.", color=discord.Color.dark_orange())
            await ctx.send(embed=embed)
    # Unban command using User ID
    @commands.command()
    @has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int = None):
        if not user_id:  # Check if user_id is provided
            embed = discord.Embed(title="Missing Required Argument", description=f"{ctx.author.mention}, please provide a valid User ID.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        user = await self.bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        embed = discord.Embed(title="Success", description=f'User {user} has been unbanned.', color=discord.Color.blurple())
        await ctx.send(embed=embed)

    # Mute command using User ID
    @commands.command(name='mute')
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, user_id: int = None, *, reason = None):
        """Mute a member or user by ID."""
        guild_id = str(ctx.guild.id)
        mute_role_id = self.mute_roles.get(guild_id)
        if not user_id:
            embed = discord.Embed(title="Missing Required Argument", description=f"{ctx.author.mention}, please provide a valid User ID.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        if not mute_role_id:
            embed = discord.Embed(title="What's your mute role?", description="I don't know what your guild mute role is. Please assign one using the `set_mute_role` command.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return
        
        mute_role = ctx.guild.get_role(int(mute_role_id))
        if not mute_role:
            embed = discord.Embed(title="Role no longer exists", description="The current mute role no longer exists. Please set a new one.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        user = await self.bot.fetch_user(user_id)
        member = ctx.guild.get_member(user.id)
    # Handle the case where member isn't found in guild.
        if not member:
            embed = discord.Embed(title="User ID not found", description=f"User ID {user_id} not found in this server. Check if the User ID is valid/correct, or that member is in this server, then try again.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        # Check if the member is already muted
        if mute_role in member.roles:
            embed = discord.Embed(title="Already muted", description=f"{member.mention} is already muted.", color=discord.Color.yellow())
            await ctx.send(embed=embed)
            return

        # Check role hierarchy
        if mute_role.position >= ctx.guild.me.top_role.position:
            embed = discord.Embed(title="Unable to assign the role", description=f"I cannot assign your guild's mute role (name: '{mute_role.name}') because it is higher than my top role. Please move my role above the mute role and try again.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        await member.add_roles(mute_role)
        embed = discord.Embed(title="Success", description=f'User {user} has been muted for reason: {reason}.', color=discord.Color.blurple())
        await ctx.send(embed=embed)


    # Unmute command using User ID
    @commands.command(name='unmute')
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, user_id: int = None, *, reason = None):
        """Unmute a member or user by ID."""
        guild_id = str(ctx.guild.id)
        mute_role_id = self.mute_roles.get(guild_id)

        if not mute_role_id:
            embed = discord.Embed(title="What's your mute role?", description="I don't know what your guild mute role is. Please assign one using the `set_mute_role` command.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        mute_role = ctx.guild.get_role(int(mute_role_id))
        if not mute_role:
            embed = discord.Embed(title="Role no longer exists", description="The current mute role no longer exists. Please set a new one.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        user = await self.bot.fetch_user(user_id)
        member = ctx.guild.get_member(user.id)
    # Handle the case where member isn't found in guild.
        if not member:
            await ctx.send(f"No member found in the guild with ID: {user_id}. Please make sure the ID is valid/correct, or that member is in the guild, then try again.")
            return

        if mute_role.position >= ctx.guild.me.top_role.position:
            embed = discord.Embed(title="Unable to remove the role", description=f"I cannot remove your guild's mute role (name: '{mute_role.name}') because it is higher than my top role. Please move my role above the mute role and try again.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        # Check if the member is currently muted
        if mute_role not in member.roles:
            embed = discord.Embed(title="Not muted", description=f"{member.mention} is not muted.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        await member.remove_roles(mute_role)
        embed = discord.Embed(title="Success", description=f'User {user} has been unmuted for reason: {reason}.', color=discord.Color.blurple())
        await ctx.send(embed=embed)

    # Timeout command using User ID
    @commands.command()
    @has_permissions(moderate_members=True)
    async def timeout(self, ctx, user_id: int = None, minutes: int = 0, *, reason=None):
        if not user_id:  # Check if user_id is provided
            embed = discord.Embed(title="Missing Required Argument", description=f"{ctx.author.mention}, please provide a valid User ID.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        user = await self.bot.fetch_user(user_id)
        member = ctx.guild.get_member(user.id)
        if member:
            duration = timedelta(minutes=minutes)
            try:
                await member.edit(timed_out_until=discord.utils.utcnow() + duration, reason=reason)
                embed = discord.Embed(title="Success", description=f'User {user} has been timed out for {minutes} munites for {reason}.', color=discord.Color.blue())
                await ctx.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(title="Denied", description=f"Couldn't timeout {member}. Make sure I have the correct permissions.", color=discord.Color.red())
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="User ID not found", description=f"User ID {user_id} not found in this server. Check if the User ID is valid/correct, or that member is in this server, then try again.", color=discord.Color.orange())
            await ctx.send(embed=embed)

    # Remove timeout command using User ID
    @commands.command()
    @has_permissions(moderate_members=True)
    async def remove_timeout(self, ctx, user_id: int = None):
        if not user_id:  # Check if user_id is provided
            embed = discord.Embed(title="Missing User ID", description="Please provide a valid User ID", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        user = await self.bot.fetch_user(user_id)
        member = ctx.guild.get_member(user.id)
        if member:
            try:
                await member.edit(timed_out_until=None)
                embed = discord.Embed(title="Success", description=f'Timeout for {user.mention} has been removed.', color=discord.Color.green())
                await ctx.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(Title="Permission Error", description=f"Couldn't remove timeout for ")
                await ctx.send(f"Couldn't remove timeout for {member.mention}. Make sure I have the correct permissions.")
        else:
            embed = discord.Embed(title="User ID not found", description=f"User ID {user_id} not found in this server. Check if the User ID is valid/correct, or that member is in this server, then try again.", color=discord.Color.orange())
            await ctx.send(embed=embed)

    # Clear command
    @commands.command()
    @has_permissions(manage_messages=True)
    async def clear(self, ctx, amount=10):
        await ctx.channel.purge(limit=amount)
        await ctx.send(f'{amount} messages cleared by {ctx.author.mention}', delete_after=5)

    # Create a mute role and override permissions in all channels
    @commands.command()
    @has_permissions(manage_roles=True, manage_channels=True)
    async def createmuterole(self, ctx, role_name: str = "Muted"):
        guild = ctx.guild

        # Check if the Muted role already exists
        existing_role = discord.utils.get(guild.roles, name=role_name)
        if existing_role:
            embed = discord.Embed(title="Role already exists", description=f'Role **{role_name}** already exists in this server. If you want to recreate and reapply {role_name} role, please delete the existing role and try again.', color=discord.Color.orange())
            await ctx.send(embed=embed)
            return

        # Create the Muted role
        mute_role = await guild.create_role(name=role_name, color=discord.Color.dark_red(), reason="Mute role created by command")


        # Initialize counters
        text_channel_count = 0
        voice_channel_count = 0
        category_count = 0


        # Set channel permissions for the Muted role
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                await channel.set_permissions(mute_role, send_messages=False)
                text_channel_count += 1
            elif isinstance(channel, discord.VoiceChannel):
                await channel.set_permissions(mute_role, speak=False)
                voice_channel_count += 1
            elif isinstance(channel, discord.CategoryChannel):
                await channel.set_permissions(mute_role, send_messages=False, speak=False)
                category_count += 1

        # Store the role name in the config
        self.config["mute_role_name"] = role_name
        self.save_config()

        # Send success message
        # Create the embed message
        embed = discord.Embed(
            title="Mute Role Permissions Set",
            description=f'Permissions for **{role_name}** have been successfully updated in the following:',
            color=discord.Color.blurple()  # You can change the color if needed
        )
        embed.add_field(name="Text Channels", value=f'{text_channel_count}')
        embed.add_field(name="Voice Channels", value=f'{voice_channel_count}')
        embed.add_field(name="Categories", value=f'{category_count}')
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)

        # Send the embed message
        await ctx.send(embed=embed)
# New set_mute_role command
    @commands.command(name='set_mute_role')
    @commands.has_permissions(administrator=True)
    async def setmuterole(self, ctx, role: discord.Role):
        """Set a custom mute role for the guild."""
        guild_id = str(ctx.guild.id)

        # Check if the mute role is already set for this guild
        if guild_id in self.mute_roles and self.mute_roles[guild_id] == str(role.id):
            embed = discord.Embed(title="Already set", description=f"The mute role is already set to {role.name} for this guild.", color=discord.color.orange())
            await ctx.send(embed=embed)
            return

        # Update the mute role for this guild
        self.mute_roles[guild_id] = str(role.id)
        self.save_mute_roles()
        embed = discord.Embed(title="Success", description=f"Role {role.name} has been set as mute role for this guild.", color=discord.Color.brand_green())
        await ctx.send(embed=embed)


   # Automod feature for word filtering
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addfilterword(self, ctx, word):
        if word not in self.config["word_filter"]:
            self.config["word_filter"].append(word)
            self.save_config()
            await ctx.send(f"Added word {word} to the word filter.")
        else:
            await ctx.send(f"The word {word} is already in the filter.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removefilterword(self, ctx, word):
        if word in self.config["word_filter"]:
            self.config["word_filter"].remove(word)
            self.save_config()
            await ctx.send(f"Removed word {word} from the word filter.")
        else:
            await ctx.send(f"The word {word} is not in the filter.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setwarnthreshold(self, ctx, threshold: int):
        self.config["warn_threshold"] = threshold
        self.save_config()
        await ctx.send(f"Warning threshold set to {threshold}.")

    @commands.Cog.listener()
    async def on_message(self, message):
    # Ignore bot's own messages or messages starting with the command prefix
        if message.author.bot or message.content.startswith(self.bot.command_prefix):
            return

        # Check for word filter (inappropriate language)
        for word in self.config["word_filter"]:
            if re.search(rf"\b{re.escape(word)}\b", message.content, re.IGNORECASE):
                # Add a warning to the user
                self.add_warning(message.author.id, f"Used filtered word '{word}'")

                # Delete the message and notify the user
                await message.delete()
                warning_msg = await message.channel.send(
                    f"{message.author.mention}, your message has been removed for using inappropriate language."
                )

                # Punish the user if they exceed the threshold
                await self.punish_user(message.author, "Using inappropriate language.")
                await warning_msg.delete(delay=10)
                return

        # Check for specific unverified Discord Nitro links while ignoring other URLs
        if "https://" in message.content:
            # Only bypass non-Nitro URLs
            if "discord.gift" not in message.content:
                return
            
            # Check for unverified Discord Nitro links
            # Regex to match valid Discord Nitro URLs (alphanumeric characters after 'discord.gift/')
            valid_gift_url = re.compile(r"https://discord\.gift/[\w\d]+$")
            
            # Handle cases where only 'https://discord.gift/' is sent or incomplete/invalid links
            if not valid_gift_url.match(message.content) or message.content.strip() == "https://discord.gift/":
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention}, sending unverified or incomplete Discord Nitro links is prohibited."
                )
                self.add_warning(message.author.id, "Sent unverified or incomplete Discord Nitro link")
                return

        user_id = message.author.id
        current_time = time.time()

        self.spam_tracker[user_id].append(current_time)
        self.spam_tracker[user_id] = [
            msg_time for msg_time in self.spam_tracker[user_id]
            if current_time - msg_time <= self.spam_interval
        ]

        if len(self.spam_tracker[user_id]) > self.spam_threshold:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, you are sending messages too quickly. Please slow down.")
            
            if self.add_warning(user_id, "Spamming messages"):
                await self.punish_user(message.author, "Spamming messages")

        # Full caps filter
        caps_count = sum(1 for c in message.content if c.isupper())
        if caps_count > 20:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, your message contains too many capital letters. Please avoid using excessive caps.")
            
            if self.add_warning(user_id, "Excessive caps"):
                await self.punish_user(message.author, "Excessive caps")

    # View warnings command
    @commands.command()
    async def warnings(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author  # Default to the command invoker if no member is specified

        user_id = str(member.id)

    # Retrieve warnings for the user from the config
        user_warnings = self.config["user_warnings"].get(user_id, [])

    # Count the number of warnings
        warning_count = len(user_warnings)

    # Prepare the embed message
        embed = discord.Embed(
        title=f"Warnings for {member.display_name}",
        description=f"{member.mention} has {warning_count} warning(s).",
        color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

        
# Clear warnings command using User ID
    @commands.command()
    @has_permissions(administrator=True)
    async def clear_warn(self, ctx, user_id: int):
        user_id_str = str(user_id)

        user = await self.bot.fetch_user(user_id)
        member = ctx.guild.get_member(user.id)

    # Check if the user has any warnings
        if user_id_str in self.config["user_warnings"]:
        # Clear the warnings
            del self.config["user_warnings"][user_id_str]
            self.save_config()
        
            embed = discord.Embed(
                title="Warnings Cleared",
                description=f"All warnings for user {user.mention} have been cleared.",
                color=discord.Color.green()
                )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="No Warnings Found",
                description=f"No warnings found for user {user.mention}.",
                color=discord.Color.orange()
                )
            await ctx.send(embed=embed)

    @commands.command()
    async def warn(self, ctx, member: discord.Member):
        user_id = str(member.id)
        if user_id in self.warnings:
            self.warnings[user_id] += 1
        else:
            self.warnings[user_id] = 1
        
        self.save_warnings()  # Save after warning

        await ctx.send(f"{member.mention} has been warned. Total warnings: {self.warnings[user_id]}")


    # Handle missing permissions
    @kick.error
    @ban.error
    @unban.error
    @mute.error
    @unmute.error
    @timeout.error
    @remove_timeout.error
    @clear.error
    async def missing_permissions_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            embed = discord.Embed(title="Prohibited!", description=f'{ctx.author.mention}, you do not have the required permissions to use this command!', color=discord.Color.red())
            await ctx.send(embed=embed)

# Setup function to add the cog (oh wow, if lacked this setup function then this cog never becomes food for the bot to eat)
async def setup(bot):
    await bot.add_cog(Moderation(bot))
