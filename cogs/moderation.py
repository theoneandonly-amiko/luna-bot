# Made with ❤️ by Lunatico Annie. Status: Finished!

import discord
from discord.ext import commands
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
import asyncio
import logging

# Configure logging according to your organization's standards
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "cogs/data/automod_config.json"
        self.mute_roles_file = "cogs/data/muteroles.json"
        self.warnings_file = "cogs/data/warnings.json"
        self.config = {}
        self.mute_roles = {}
        self.warnings = {}
        self.spam_tracker = defaultdict(list)
        self.spam_threshold = 5  # Max messages within the interval
        self.spam_interval = 10  # Time window in seconds
        self.mention_threshold = 5  # mentions
        self.image_spam_tracker = defaultdict(list)
        self.image_spam_interval = 10  # seconds
        self.image_spam_threshold = 3  # images

        # Load data
        self.load_config()
        self.load_mute_roles()
        self.load_warnings()

    def load_config(self):
        """Load the automod configuration."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    "word_filter": [],
                    "warn_threshold": 3,
                    "user_warnings": {},
                    "mute_role_name": "Muted"
                }
                self.save_config()
        except Exception:
            logger.exception("Failed to load config:")
            self.config = {
                "word_filter": [],
                "warn_threshold": 3,
                "user_warnings": {},
                "mute_role_name": "Muted"
            }

    def save_config(self):
        """Save the automod configuration."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception:
            logger.exception("Failed to save config:")

    def load_mute_roles(self):
        """Load existing mute roles from the JSON file."""
        try:
            if os.path.exists(self.mute_roles_file):
                with open(self.mute_roles_file, 'r') as f:
                    self.mute_roles = json.load(f)
            else:
                self.mute_roles = {}
        except Exception:
            logger.exception("Failed to load mute roles:")
            self.mute_roles = {}

    def save_mute_roles(self):
        """Save mute roles to the JSON file."""
        try:
            with open(self.mute_roles_file, 'w') as f:
                json.dump(self.mute_roles, f, indent=4)
        except Exception:
            logger.exception("Failed to save mute roles:")

    def load_warnings(self):
        """Load user warnings from the JSON file."""
        try:
            if os.path.exists(self.warnings_file):
                with open(self.warnings_file, 'r') as f:
                    self.warnings = json.load(f)
            else:
                self.warnings = {}
        except Exception:
            logger.exception("Failed to load warnings:")
            self.warnings = {}

    def save_warnings(self):
        """Save user warnings to the JSON file."""
        try:
            with open(self.warnings_file, 'w') as f:
                json.dump(self.warnings, f, indent=4)
        except Exception:
            logger.exception("Failed to save warnings:")

    def add_warning(self, user_id: int, reason: str):
        """Add a warning to a user."""
        user_id_str = str(user_id)
        if user_id_str not in self.warnings:
            self.warnings[user_id_str] = []
        self.warnings[user_id_str].append({
            "reason": reason,
            "time": datetime.now(timezone.utc).isoformat()
        })
        self.save_warnings()
        warn_count = len(self.warnings[user_id_str])
        warn_threshold = self.config.get("warn_threshold", 3)
        return warn_count >= warn_threshold

    async def punish_user(self, member, reason):
        """Punish the user after exceeding warn threshold."""
        warn_count = len(self.warnings.get(str(member.id), []))
        warn_threshold = self.config.get("warn_threshold", 3)
        if warn_count >= warn_threshold:
            guild_id = str(member.guild.id)
            mute_role = None
            mute_role_id = self.mute_roles.get(guild_id)
            if mute_role_id:
                mute_role = member.guild.get_role(int(mute_role_id))
            else:
                # Create or get default 'Muted' role
                mute_role_name = self.config.get("mute_role_name", "Muted")
                mute_role = discord.utils.get(member.guild.roles, name=mute_role_name)
                if not mute_role:
                    mute_role = await self.create_mute_role(member.guild, mute_role_name)

            # Assign the mute role to the user
            await member.add_roles(mute_role, reason=reason)
            try:
                embed = discord.Embed(
                    title="You have been muted",
                    description=f"You have been muted in **{member.guild.name}** for: {reason}",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                await member.send(embed=embed)
            except discord.Forbidden:
                pass

    async def create_mute_role(self, guild, role_name):
        """Create a mute role with appropriate permissions."""
        try:
            mute_role = await guild.create_role(name=role_name, reason="Mute role created by bot")
            channels_updated = 0
            categories_updated = 0
            for channel in guild.channels:
                await channel.set_permissions(mute_role, send_messages=False, speak=False)
                channels_updated += 1
            for category in guild.categories:
                await category.set_permissions(mute_role, send_messages=False, speak=False)
                categories_updated += 1
            # Send an embed message about the updates
            embed = discord.Embed(
                title="Mute Role Created",
                description=f"Role **{mute_role.name}** has been created and configured.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Channels Updated", value=str(channels_updated), inline=True)
            embed.add_field(name="Categories Updated", value=str(categories_updated), inline=True)
            if guild.system_channel:
                await guild.system_channel.send(embed=embed)
            return mute_role
        except Exception:
            logger.exception("Failed to create mute role:")
            return None

    def parse_duration(self, duration_str):
        """Parse a duration string and return the total seconds."""
        regex = re.compile(r'(?P<value>\d+)(?P<unit>[smhd])')
        matches = regex.findall(duration_str.lower())
        total_seconds = 0
        for value, unit in matches:
            value = int(value)
            if unit == 's':
                total_seconds += value
            elif unit == 'm':
                total_seconds += value * 60
            elif unit == 'h':
                total_seconds += value * 3600
            elif unit == 'd':
                total_seconds += value * 86400
        return total_seconds

    async def resolve_user(self, ctx, user_input):
        """Resolve a user input to a discord.Member or discord.User."""
        try:
            # Try to get member by mention or ID
            user = await commands.MemberConverter().convert(ctx, user_input)
            return user
        except commands.MemberNotFound:
            pass
        try:
            # Try to get user by ID
            user_id = int(user_input)
            user = await self.bot.fetch_user(user_id)
            return user
        except (ValueError, discord.NotFound):
            pass
        return None

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, user_input: str = None, *, reason=None):
        """Kick a member by mention or user ID."""
        if not user_input:
            embed = discord.Embed(
                title="Missing User",
                description="Please mention a user or provide a valid User ID.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        user = await self.resolve_user(ctx, user_input)
        if not user:
            embed = discord.Embed(title="Who is this?", description="I cannot find this user. Try again.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            return
        member = ctx.guild.get_member(user.id)
        if member:
            try:
                await member.kick(reason=reason)
                embed = discord.Embed(
                    title="Member Kicked",
                    description=f"User {member.mention} has been kicked.",
                    color=discord.Color.orange(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Reason", value=reason or "No reason provided.", inline=False)
                await ctx.send(embed=embed)
                try:
                    dm_embed = discord.Embed(
                        title="You have been kicked",
                        description=f"You have been kicked from **{ctx.guild.name}**.",
                        color=discord.Color.red(),
                        timestamp=datetime.now(timezone.utc)
                    )
                    dm_embed.add_field(name="Reason", value=reason or "No reason provided.", inline=False)
                    await user.send(embed=dm_embed)
                except discord.Forbidden:
                    pass
            except Exception as e:
                embed = discord.Embed(title="Error!", description=f"An error occurred while trying to kick the user: {e}", color=discord.Color.red())
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="User not found.", description="User is not in the guild.", color=discord.Color.orange())
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user_input: str = None, *, reason=None):
        """Ban a user by mention or User ID."""
        if not user_input:
            embed = discord.Embed(
                title="Missing User",
                description="Please mention a user or provide a valid User ID.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        user = await self.resolve_user(ctx, user_input)
        if not user:
            await ctx.send("User not found.")
            return
        try:
            # Check if user is already banned
            is_banned = False
            async for ban_entry in ctx.guild.bans():
                if ban_entry.user.id == user.id:
                    is_banned = True
                    break
            if is_banned:
                embed = discord.Embed(
                    title="User Already Banned",
                    description=f"User {user.mention} is already banned.",
                    color=discord.Color.orange(),
                    timestamp=datetime.now(timezone.utc)
                )
                await ctx.send(embed=embed)
                return
            await ctx.guild.ban(user, reason=reason)
            embed = discord.Embed(
                title="Member Banned",
                description=f"User {user.mention} has been banned.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Reason", value=reason or "No reason provided.", inline=False)
            await ctx.send(embed=embed)
            try:
                dm_embed = discord.Embed(
                    title="You have been banned",
                    description=f"You have been banned from **{ctx.guild.name}**.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                dm_embed.add_field(name="Reason", value=reason or "No reason provided.", inline=False)
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass
        except Exception as e:
            embed = discord.Embed(title="Failed.", description=f"An error occurred while trying to ban the user: {e}", color=discord.Color.red())
            await ctx.send(embed=embed)
            
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_input: str = None):
        """Unban a user by mention or User ID."""
        if not user_input:
            embed = discord.Embed(
                title="Missing User",
                description="Please mention a user or provide a valid User ID.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        user = await self.resolve_user(ctx, user_input)
        if not user:
            await ctx.send("User not found.")
            return
        try:
            # Check if user is actually banned
            is_banned = False
            async for ban_entry in ctx.guild.bans():
                if ban_entry.user.id == user.id:
                    is_banned = True
                    break
            if not is_banned:
                embed = discord.Embed(
                    title="User Not Banned",
                    description=f"User {user.mention} is not banned.",
                    color=discord.Color.orange(),
                    timestamp=datetime.now(timezone.utc)
                )
                await ctx.send(embed=embed)
                return
            await ctx.guild.unban(user)
            embed = discord.Embed(
                title="Member Unbanned",
                description=f"User {user.mention} has been unbanned.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Failed.", description=f"An error occurred while trying to ban the user: {e}", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, user_input: str = None, duration: str = None, *, reason=None):
        """Mute a member by mention or User ID for a specified duration."""
        if not user_input:
            await ctx.send("Please mention a user or provide a valid User ID.")
            return
        guild_id = str(ctx.guild.id)
        mute_role_id = self.mute_roles.get(guild_id)
        if not mute_role_id:
            await ctx.send("Mute role is not set. Please use the `setmuterole` command to set it.")
            return
        mute_role = ctx.guild.get_role(int(mute_role_id))
        if not mute_role:
            await ctx.send("Mute role not found. Please set a valid mute role.")
            return
        user = await self.resolve_user(ctx, user_input)
        if not user:
            await ctx.send("User not found.")
            return
        member = ctx.guild.get_member(user.id)
        if not member:
            await ctx.send("User not found in the guild.")
            return
        if mute_role in member.roles:
            embed = discord.Embed(
                title="Member Already Muted",
                description=f"User {member.mention} is already muted.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            return
        try:
            await member.add_roles(mute_role, reason=reason)
            embed = discord.Embed(
                title="Member Muted",
                description=f"User {member.mention} has been muted.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Reason", value=reason or "No reason provided.", inline=False)
            await ctx.send(embed=embed)
            if duration:
                total_seconds = self.parse_duration(duration)
                if total_seconds:
                    await asyncio.sleep(total_seconds)
                    await member.remove_roles(mute_role, reason="Mute duration expired.")
                    unmute_embed = discord.Embed(
                        title="Member Unmuted",
                        description=f"User {member.mention} has been unmuted.",
                        color=discord.Color.green(),
                        timestamp=datetime.now(timezone.utc)
                    )
                    await ctx.send(embed=unmute_embed)
            try:
                dm_embed = discord.Embed(
                    title="You have been muted",
                    description=f"You have been muted in **{ctx.guild.name}**.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                dm_embed.add_field(name="Reason", value=reason or "No reason provided.", inline=False)
                if duration:
                    dm_embed.add_field(name="Duration", value=duration, inline=False)
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass
        except Exception as e:
            failed_embed = discord.Embed(title="Failed", description=f"An error occurred while trying to mute the user: {e}", color=discord.Color.red())
            await ctx.send(embed=failed_embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, user_input: str = None):
        """Unmute a member by mention or User ID."""
        if not user_input:
            await ctx.send("Please mention a user or provide a valid User ID.")
            return
        guild_id = str(ctx.guild.id)
        mute_role_id = self.mute_roles.get(guild_id)
        if not mute_role_id:
            await ctx.send("Mute role is not set. Please use the `setmuterole` command to set it.")
            return
        mute_role = ctx.guild.get_role(int(mute_role_id))
        if not mute_role:
            await ctx.send("Mute role not found. Please set a valid mute role.")
            return
        user = await self.resolve_user(ctx, user_input)
        if not user:
            await ctx.send("User not found.")
            return
        member = ctx.guild.get_member(user.id)
        if not member:
            await ctx.send("User not found in the guild.")
            return
        if mute_role not in member.roles:
            embed = discord.Embed(
                title="Member Not Muted",
                description=f"User {member.mention} is not muted.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            return
        try:
            await member.remove_roles(mute_role, reason="Unmute command issued.")
            embed = discord.Embed(
                title="Member Unmuted",
                description=f"User {member.mention} has been unmuted.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            try:
                dm_embed = discord.Embed(
                    title="You have been unmuted",
                    description=f"You have been unmuted in **{ctx.guild.name}**.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass
        except Exception as e:
            failed_embed = discord.Embed(title="Failed", description=f"An error occurred while trying to unmute the user: {e}", color=discord.Color.red())
            await ctx.send(embed=failed_embed)

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, user_input: str = None, duration: str = None, *, reason=None):
        """Timeout a member by mention or User ID for a specified duration."""
        if not user_input or not duration:
            await ctx.send("Please mention a user or provide a valid User ID and duration.")
            return
        user = await self.resolve_user(ctx, user_input)
        if not user:
            await ctx.send("User not found.")
            return
        member = ctx.guild.get_member(user.id)
        if not member:
            await ctx.send("User not found in the guild.")
            return
        try:
            total_seconds = self.parse_duration(duration)
            if not total_seconds:
                await ctx.send("Invalid duration format.")
                return
            until_time = discord.utils.utcnow() + timedelta(seconds=total_seconds)
            await member.edit(timed_out_until=until_time, reason=reason)
            embed = discord.Embed(
                title="Member Timed Out",
                description=f"User {member.mention} has been timed out for {duration}.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Reason", value=reason or "No reason provided.", inline=False)
            await ctx.send(embed=embed)
            try:
                dm_embed = discord.Embed(
                    title="You have been timed out",
                    description=f"You have been timed out in **{ctx.guild.name}** for {duration}.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                dm_embed.add_field(name="Reason", value=reason or "No reason provided.", inline=False)
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass
        except Exception as e:
            failed_embed = discord.Embed(title="Failed", description=f"An error occurred while trying to timeout the user: {e}", color=discord.Color.red())
            await ctx.send(embed=failed_embed)

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def remove_timeout(self, ctx, user_input: str = None):
        """Remove timeout from a member by mention or User ID."""
        if not user_input:
            await ctx.send("Please mention a user or provide a valid User ID.")
            return
        user = await self.resolve_user(ctx, user_input)
        if not user:
            await ctx.send("User not found.")
            return
        member = ctx.guild.get_member(user.id)
        if not member:
            await ctx.send("User not found in the guild.")
            return
        try:
            await member.edit(timed_out_until=None, reason="Timeout removed.")
            embed = discord.Embed(
                title="Timeout Removed",
                description=f"Timeout for {member.mention} has been removed.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            try:
                dm_embed = discord.Embed(
                    title="Your timeout has been removed",
                    description=f"Your timeout in **{ctx.guild.name}** has been removed.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass
        except Exception as e:
            failed_embed = discord.Embed(title="Failed", description=f"An error occurred while trying to remove the timeout: {e}", color=discord.Color.red())
            await ctx.send(embed=failed_embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount='10'):
        """Clear a number of messages from the channel."""
        try:
            if str(amount).lower() == 'all':
                deleted = await ctx.channel.purge(limit=None)
                embed = discord.Embed(
                    title="Messages Cleared",
                    description=f"All possible messages have been cleared: ({len(deleted)} messages).",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
            else:
                amount = int(amount)
                deleted = await ctx.channel.purge(limit=amount)
                embed = discord.Embed(
                    title="Messages Cleared",
                    description=f"{len(deleted)} messages have been cleared.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
            await ctx.send(embed=embed, delete_after=5)
        except ValueError:
            embed = discord.Embed(title="Invalid input.", description="Please provide a valid integer amount or 'all'.", color=discord.Color.orange())
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            if e.code == 50034:
                embed = discord.Embed(title="Reached Limitation!", description="Cannot delete messages older than 14 days.", color=discord.Color.yellow())
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="Failed.", description=f"An error occurred while trying to clear messages: {e}", color=discord.Color.red())
                await ctx.send(embed=embed)
        except Exception as h:
            embed = discord.Embed(title="Failed.", description=f"An error occurred while trying to clear messages: {h}")
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True, manage_channels=True)
    async def createmuterole(self, ctx, role_name: str = "Muted"):
        """Create a mute role and set appropriate permissions."""
        guild = ctx.guild
        existing_role = discord.utils.get(guild.roles, name=role_name)
        if existing_role:
            embed = discord.Embed(
                title="Role Exists",
                description=f"Role **{role_name}** already exists.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            return
        try:
            mute_role = await guild.create_role(name=role_name, reason="Mute role created by bot")
            channels_updated = 0
            categories_updated = 0
            for channel in guild.channels:
                await channel.set_permissions(mute_role, send_messages=False, speak=False)
                channels_updated += 1
            for category in guild.categories:
                await category.set_permissions(mute_role, send_messages=False, speak=False)
                categories_updated += 1

            guild_id = str(guild.id)
            self.mute_roles[guild_id] = str(mute_role.id)
            self.save_mute_roles()

            embed = discord.Embed(
                title="Mute Role Created",
                description=f"Role **{mute_role.name}** has been created and set as mute role.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Channels Updated", value=str(channels_updated), inline=True)
            embed.add_field(name="Categories Updated", value=str(categories_updated), inline=True)
            await ctx.send(embed=embed)
        except Exception as e:
            failed_embed = discord.Embed(title="Failed", description=f"An error occurred while trying to create the mute role: {e}", color=discord.Color.red())
            await ctx.send(embed=failed_embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setmuterole(self, ctx, role: discord.Role):
        """Set a custom mute role for the guild."""
        guild_id = str(ctx.guild.id)
        self.mute_roles[guild_id] = str(role.id)
        self.save_mute_roles()
        embed = discord.Embed(
            title="Mute Role Set",
            description=f"Role **{role.name}** has been set as the mute role.",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addfilterword(self, ctx, word: str):
        """Add a word to the word filter."""
        word_filter = self.config.get("word_filter", [])
        if word.lower() not in word_filter:
            word_filter.append(word.lower())
            self.config["word_filter"] = word_filter
            self.save_config()
            embed = discord.Embed(
                title="Word Added",
                description=f"Word '{word}' has been added to the filter.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Word Already Exists",
                description=f"Word '{word}' is already in the filter.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removefilterword(self, ctx, word: str):
        """Remove a word from the word filter."""
        word_filter = self.config.get("word_filter", [])
        if word.lower() in word_filter:
            word_filter.remove(word.lower())
            self.config["word_filter"] = word_filter
            self.save_config()
            embed = discord.Embed(
                title="Word Removed",
                description=f"Word '{word}' has been removed from the filter.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Word Not Found",
                description=f"Word '{word}' is not in the filter.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setwarnthreshold(self, ctx, threshold: int):
        """Set the warning threshold."""
        self.config["warn_threshold"] = threshold
        self.save_config()
        embed = discord.Embed(
            title="Warning Threshold Set",
            description=f"Warning threshold has been set to {threshold}.",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def warnings(self, ctx, member: discord.Member = None):
        """View warnings for a member."""
        if member is None:
            member = ctx.author
        user_id_str = str(member.id)
        user_warnings = self.warnings.get(user_id_str, [])
        warn_count = len(user_warnings)
        if warn_count > 0:
            embed = discord.Embed(
                title=f"Warnings for {member.display_name}",
                description=f"{member.mention} has {warn_count} warning(s).",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            for idx, warning in enumerate(user_warnings, start=1):
                embed.add_field(
                    name=f"Warning {idx}",
                    value=f"Reason: {warning['reason']}\nTime: {warning['time']}",
                    inline=False
                )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="No Warnings",
                description=f"{member.mention} has no warnings.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearwarn(self, ctx, user_input: str):
        """Clear warnings for a user by mention or User ID."""
        user = await self.resolve_user(ctx, user_input)
        if not user:
            await ctx.send("User not found.")
            return
        user_id_str = str(user.id)
        if user_id_str in self.warnings:
            del self.warnings[user_id_str]
            self.save_warnings()
            embed = discord.Embed(
                title="Warnings Cleared",
                description=f"All warnings for {user.mention} have been cleared.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="No Warnings Found",
                description=f"No warnings found for {user.mention}.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member."""
        if member == ctx.author:
            embed = discord.Embed(
                title="Action Prohibited",
                description="You cannot warn yourself.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            return
        if self.add_warning(member.id, reason):
            await self.punish_user(member, reason)
            embed = discord.Embed(
                title="Member Warned and Muted",
                description=f"{member.mention} has been warned and muted for exceeding warn threshold.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Member Warned",
                description=f"{member.mention} has been warned.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)



    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Reapply mute role if a muted member rejoins."""
        guild_id = str(member.guild.id)
        mute_role_id = self.mute_roles.get(guild_id)
        if mute_role_id:
            mute_role = member.guild.get_role(int(mute_role_id))
            if mute_role and str(member.id) in self.warnings:
                await member.add_roles(mute_role)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Automod features implemented through message listener."""
        if message.author.bot:
            return
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return  # Ignore messages that are commands
        
        current_time = time.time()
        user_id_str = str(message.author.id)
        
        # Mention spam protection
        mention_count = len(message.mentions) + len(message.role_mentions)
        if mention_count > self.mention_threshold:
            await message.delete()
            embed = discord.Embed(
                title="Excessive Mentions",
                description=f"{message.author.mention}, please avoid mentioning too many users or roles.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await message.channel.send(embed=embed)
            if self.add_warning(message.author.id, "Excessive mentions"):
                await self.punish_user(message.author, "Excessive mentions.")
            return

        # Word filter
        word_filter = self.config.get("word_filter", [])
        for word in word_filter:
            pattern = re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE)
            if pattern.search(message.content):
                await message.delete()
                embed = discord.Embed(
                    title="Prohibited Word Used",
                    description=f"{message.author.mention}, you used a prohibited word.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                await message.channel.send(embed=embed)
                if self.add_warning(message.author.id, f"Used prohibited word: {word}"):
                    await self.punish_user(message.author, "Used prohibited words.")
                return
            
        # Spam detection
        self.spam_tracker[message.author.id].append(current_time)
        self.spam_tracker[message.author.id] = [
            t for t in self.spam_tracker[message.author.id]
            if current_time - t <= self.spam_interval
        ]
        if len(self.spam_tracker[message.author.id]) > self.spam_threshold:
            await message.delete()
            embed = discord.Embed(
                title="Please Stop Spamming",
                description=f"{message.author.mention}, please stop spamming.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await message.channel.send(embed=embed)
            if self.add_warning(message.author.id, "Spamming messages"):
                await self.punish_user(message.author, "Spamming messages.")
            return

        # Caps filter
        caps_count = sum(1 for c in message.content if c.isupper())
        if len(message.content) > 10 and (caps_count / len(message.content)) > 0.7:
            await message.delete()
            embed = discord.Embed(
                title="Excessive Capital Letters",
                description=f"{message.author.mention}, please avoid using excessive capital letters.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            await message.channel.send(embed=embed)
            if self.add_warning(message.author.id, "Excessive capital letters"):
                await self.punish_user(message.author, "Excessive capital letters.")
            return

        # Invite link detection
        invite_pattern = re.compile(r'discord(?:\.gg|app\.com/invite)/[\w-]+')
        if invite_pattern.search(message.content):
            await message.delete()
            embed = discord.Embed(
                title="Invite Link Detected",
                description=f"{message.author.mention}, please do not post invite links.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await message.channel.send(embed=embed)
            if self.add_warning(message.author.id, "Posted invite link"):
                await self.punish_user(message.author, "Posted invite link.")
            return

        # Image spam detection
        if len(message.attachments) > 0:
            self.image_spam_tracker[message.author.id].append(current_time)
            self.image_spam_tracker[message.author.id] = [
                t for t in self.image_spam_tracker[message.author.id]
                if current_time - t <= self.image_spam_interval
            ]
            if len(self.image_spam_tracker[message.author.id]) > self.image_spam_threshold:
                await message.delete()
                embed = discord.Embed(
                    title="Image Spam Detected",
                    description=f"{message.author.mention}, please stop spamming images.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                await message.channel.send(embed=embed)
                if self.add_warning(message.author.id, "Image spamming"):
                    await self.punish_user(message.author, "Image spamming.")
                return

        # Repeated text detection
        words = message.content.split()
        if len(words) > 5:
            word_counts = Counter(words)
            most_common_word, count = word_counts.most_common(1)[0]
            if count > 5 and (count / len(words)) > 0.5:
                await message.delete()
                embed = discord.Embed(
                    title="Repeated Text Detected",
                    description=f"{message.author.mention}, please avoid repeating the same word or phrase excessively.",
                    color=discord.Color.orange(),
                    timestamp=datetime.now(timezone.utc)
                )
                await message.channel.send(embed=embed)
                if self.add_warning(message.author.id, "Repeated text"):
                    await self.punish_user(message.author, "Repeated text.")
                return

        # Unverified Discord Nitro links
        if "https://" in message.content:
            if "discord.gift/" in message.content:
                valid_gift_url = re.compile(r'https://discord\.gift/[\w\d]+$')
                if not valid_gift_url.match(message.content.strip()):
                    await message.delete()
                    embed = discord.Embed(
                        title="Unverified Discord Nitro Link",
                        description=f"{message.author.mention}, sending unverified or incomplete Discord Nitro links is prohibited.",
                        color=discord.Color.red(),
                        timestamp=datetime.now(timezone.utc)
                    )
                    await message.channel.send(embed=embed)
                    if self.add_warning(message.author.id, "Sent unverified Discord Nitro link"):
                        await self.punish_user(message.author, "Sent unverified Discord Nitro links.")
                    return

    @kick.error
    @ban.error
    @unban.error
    @mute.error
    @warn.error
    @clearwarn.error
    @unmute.error
    @timeout.error
    @remove_timeout.error
    @clear.error
    async def command_error_handler(self, ctx, error):
        """Handle errors for moderation commands."""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Permission Denied",
                description=f"{ctx.author.mention}, you do not have permission to use this command.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        else:
            logger.exception("An error occurred:")
            embed = discord.Embed(
                title="Error",
                description="An error occurred while processing the command.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))