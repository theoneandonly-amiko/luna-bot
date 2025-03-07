# Made with ❤️ by Lunatico Annie. Status: Finished!

import discord
from discord.ext import commands
import json
import os
import re
from datetime import datetime, timedelta, timezone
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mute_roles_file = "cogs/data/muteroles.json"
        self.warnings_file = "cogs/data/warnings.json"
        self.log_channels_file = "cogs/data/logchannels.json"
        self.muted_users_file = "cogs/data/muted_users.json"
        self.muted_users = {}
        self.mute_roles = {}
        self.warnings = {}
        self.log_channels = {}
        self.load_mute_roles()
        self.load_muted_users()
        self.load_warnings()
        self.load_log_channels()

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

    def load_muted_users(self):
        """Load muted users from the JSON file."""
        try:
            if os.path.exists(self.muted_users_file):
                with open(self.muted_users_file, 'r') as f:
                    self.muted_users = json.load(f)
            else:
                self.muted_users = {}
        except Exception:
            logger.exception("Failed to load muted users:")
            self.muted_users = {}

    def save_muted_users(self):
        """Save muted users to the JSON file."""
        try:
            with open(self.muted_users_file, 'w') as f:
                json.dump(self.muted_users, f, indent=4)
        except Exception:
            logger.exception("Failed to save muted users:")

# Add these new methods for log channel management
    def load_log_channels(self):
        """Load log channels from the JSON file."""
        try:
            if os.path.exists(self.log_channels_file):
                with open(self.log_channels_file, 'r') as f:
                    self.log_channels = json.load(f)
            else:
                self.log_channels = {}
        except Exception:
            logger.exception("Failed to load log channels:")
            self.log_channels = {}

    def save_log_channels(self):
        """Save log channels to the JSON file."""
        try:
            with open(self.log_channels_file, 'w') as f:
                json.dump(self.log_channels, f, indent=4)
        except Exception:
            logger.exception("Failed to save log channels:")

    async def log_action(self, guild, embed):
        """Send log message to the designated log channel."""
        if not guild:
            return
            
        guild_id = str(guild.id)
        if guild_id not in self.log_channels:
            return
            
        try:
            channel = self.bot.get_channel(int(self.log_channels[guild_id]))
            if channel:
                await channel.send(embed=embed)
        except Exception:
            logger.exception("Failed to send log message:")

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

        user_id_str = str(member.id)
        if user_id_str not in self.warnings:
            self.warnings[user_id_str] = []
            
        self.warnings[user_id_str].append({
            "reason": reason,
            "time": datetime.now(timezone.utc).isoformat()
        })
        self.save_warnings()

        embed = discord.Embed(
            title="Member Warned",
            description=f"{member.mention} has been warned.",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Reason", value=reason, inline=False)
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
        """Clear warnings for a user."""
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
            user = await commands.MemberConverter().convert(ctx, user_input)
            return user
        except commands.MemberNotFound:
            pass
        try:
            user_id = int(user_input)
            user = await self.bot.fetch_user(user_id)
            return user
        except (ValueError, discord.NotFound):
            pass
        return None

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

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, user_input: str = None, *, reason=None):
        """Kick a member by mention or user ID."""
        if not user_input:
            embed = discord.Embed(
                title="⚠️ Kick Command",
                description="Please mention a user or provide a valid User ID.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        user = await self.resolve_user(ctx, user_input)
        if not user:
            embed = discord.Embed(
                title="❌ User Not Found",
                description="I cannot find this user. Please check the ID/mention and try again.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        member = ctx.guild.get_member(user.id)
        if member:
            try:
                await member.kick(reason=reason)
                embed = discord.Embed(
                    title="👢 Member Kicked",
                    description=f"{member.mention} has been kicked from the server.",
                    color=discord.Color.brand_green(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Kicked User", value=f"{member} ({member.id})", inline=False)
                embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                embed.set_footer(text=f"Kicked by {ctx.author}")
                await ctx.send(embed=embed)

                log_embed = discord.Embed(
                    title="👢 Member Kicked",
                    description=f"{user.mention} has been kicked from the server.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                log_embed.add_field(name="User", value=f"{user}", inline=True)
                log_embed.add_field(name="Moderator", value=f"{ctx.author}", inline=True)
                log_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                await self.log_action(ctx.guild, log_embed)

                try:
                    dm_embed = discord.Embed(
                        title="You Have Been Kicked",
                        description=f"You have been kicked from **{ctx.guild.name}**",
                        color=discord.Color.red(),
                        timestamp=datetime.now(timezone.utc)
                    )
                    dm_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                    dm_embed.add_field(name="Kicked By", value=str(ctx.author), inline=False)
                    await user.send(embed=dm_embed)
                except discord.Forbidden:
                    pass

            except Exception as e:
                error_embed = discord.Embed(
                    title="❌ Kick Failed",
                    description="An error occurred while trying to kick the user.",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                error_embed.add_field(name="Error Details", value=str(e), inline=False)
                error_embed.set_footer(text=f"Requested by {ctx.author}")
                await ctx.send(embed=error_embed)
        else:
            embed = discord.Embed(
                title="❌ User Not Found",
                description="This user is not in the server.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user_input: str = None, *, reason=None):
        """Ban a user by mention or User ID."""
        if not user_input:
            embed = discord.Embed(
                title="⚠️ Ban Command",
                description="Please mention a user or provide a valid User ID.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        user = await self.resolve_user(ctx, user_input)
        if not user:
            embed = discord.Embed(
                title="❌ User Not Found",
                description="I cannot find this user. Please check the ID/mention and try again.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
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
                    title="⚠️ Already Banned",
                    description=f"{user.mention} is already banned from this server.",
                    color=discord.Color.orange(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.set_footer(text=f"Requested by {ctx.author}")
                await ctx.send(embed=embed)
                return

            await ctx.guild.ban(user, reason=reason)
            embed = discord.Embed(
                title="🔨 Member Banned",
                description=f"{user.mention} has been banned from the server.",
                color=discord.Color.brand_green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Banned User", value=f"{user} ({user.id})", inline=False)
            embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            embed.set_footer(text=f"Banned by {ctx.author}")
            await ctx.send(embed=embed)

            # Inside ban command, after successful ban
            log_embed = discord.Embed(
                title="🔨 Member Banned",
                description=f"{user.mention} has been banned from the server.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            log_embed.add_field(name="User", value=f"{user}", inline=True)
            log_embed.add_field(name="Moderator", value=f"{ctx.author}", inline=True)
            log_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            await self.log_action(ctx.guild, log_embed)

            try:
                dm_embed = discord.Embed(
                    title="You Have Been Banned",
                    description=f"You have been banned from **{ctx.guild.name}**",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                dm_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                dm_embed.add_field(name="Banned By", value=str(ctx.author), inline=False)
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Ban Failed",
                description="An error occurred while trying to ban the user.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            error_embed.add_field(name="Error Details", value=str(e), inline=False)
            error_embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=error_embed)
            
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_input: str = None):
        """Unban a user by User ID."""
        if not user_input:
            embed = discord.Embed(
                title="⚠️ Unban Command",
                description="Please provide a valid User ID.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        try:
            # Check if user is actually banned
            user = await self.bot.fetch_user(int(user_input))
            is_banned = False
            async for ban_entry in ctx.guild.bans():
                if ban_entry.user.id == user.id:
                    is_banned = True
                    break

            if not is_banned:
                embed = discord.Embed(
                    title="⚠️ Not Banned",
                    description=f"User {user.mention} is not banned from this server.",
                    color=discord.Color.orange(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.set_footer(text=f"Requested by {ctx.author}")
                await ctx.send(embed=embed)
                return

            await ctx.guild.unban(user)
            embed = discord.Embed(
                title="🔓 Member Unbanned",
                description=f"{user.mention} has been unbanned from the server.",
                color=discord.Color.brand_green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Unbanned User", value=f"{user}", inline=False)
            embed.set_footer(text=f"Unbanned by {ctx.author}")
            await ctx.send(embed=embed)
            
            log_embed = discord.Embed(
                title="🔓 Member Unbanned",
                description=f"{user.mention} has been unbanned from the server.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            log_embed.add_field(name="User", value=f"{user}", inline=True)
            log_embed.add_field(name="Moderator", value=f"{ctx.author}", inline=True)
            await self.log_action(ctx.guild, log_embed)
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Please provide a valid user ID.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)

        except discord.NotFound:
            embed = discord.Embed(
                title="❌ User Not Found",
                description="Could not find a user with that ID.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Unban Failed",
                description="An error occurred while trying to unban the user.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            error_embed.add_field(name="Error Details", value=str(e), inline=False)
            error_embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=error_embed)

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, user_input: str = None, *, reason_or_duration: str = None):
        """Timeout a member for a specified duration."""
        if not user_input:
            embed = discord.Embed(
                title="⚠️ Timeout Command",
                description="Please mention a user or provide a valid User ID.\nExample: `!timeout @user [duration] [reason]`",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Duration Format", value="Use: s (seconds), m (minutes), h (hours), d (days)\nExample: 1h30m", inline=False)
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        # Parse duration and reason
        duration = None
        reason = None
        if reason_or_duration:
            # Split the first word to check if it's a duration
            parts = reason_or_duration.split(maxsplit=1)
            first_word = parts[0]
            
            # Check if the first word matches duration pattern
            if re.match(r'^\d+[smhd](?:\d+[smhd])*$', first_word):
                duration = first_word
                reason = parts[1] if len(parts) > 1 else None
            else:
                # If first word isn't a duration, treat entire string as reason
                reason = reason_or_duration



        user = await self.resolve_user(ctx, user_input)
        if not user:
            embed = discord.Embed(
                title="❌ User Not Found",
                description="I cannot find this user. Please check the ID/mention and try again.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        member = ctx.guild.get_member(user.id)
        if not member:
            embed = discord.Embed(
                title="❌ User Not in Server",
                description="This user is not in the server.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        if not duration:
            embed = discord.Embed(
                title="❌ Duration Required",
                description="Please provide a valid duration for the timeout.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Format", value="Use: s (seconds), m (minutes), h (hours), d (days)\nExample: 1h30m", inline=False)
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        total_seconds = self.parse_duration(duration)
        if not total_seconds:
            embed = discord.Embed(
                title="❌ Invalid Duration",
                description="Please provide a valid duration format.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Format", value="Use: s (seconds), m (minutes), h (hours), d (days)\nExample: 1h30m", inline=False)
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        try:
            until_time = discord.utils.utcnow() + timedelta(seconds=total_seconds)
            await member.timeout(until_time, reason=reason)
            
            embed = discord.Embed(
                title="⏰ Member Timed Out",
                description=f"{member.mention} has been timed out.",
                color=discord.Color.brand_green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Duration", value=duration, inline=True)
            embed.add_field(name="Expires", value=f"<t:{int(until_time.timestamp())}:R>", inline=True)
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Timed out by {ctx.author}")
            await ctx.send(embed=embed)
            
            log_embed = discord.Embed(
                title="⏰ Member Timed out",
                description=f"{user.mention} has been timed out.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            log_embed.add_field(name="User", value=f"{user}", inline=True)
            log_embed.add_field(name="Duration", value=duration, inline=True)
            log_embed.add_field(name="Expires", value=f"<t:{int(until_time.timestamp())}:R>", inline=True)
            log_embed.add_field(name="Moderator", value=f"{ctx.author}", inline=True)
            log_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
            await self.log_action(ctx.guild, log_embed)
            
            try:
                dm_embed = discord.Embed(
                    title="You Have Been Timed Out",
                    description=f"You have been timed out in **{ctx.guild.name}**",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                dm_embed.add_field(name="Duration", value=duration, inline=True)
                dm_embed.add_field(name="Expires", value=f"<t:{int(until_time.timestamp())}:R>", inline=True)
                dm_embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Timeout Failed",
                description="An error occurred while trying to timeout the user.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            error_embed.add_field(name="Error Details", value=str(e), inline=False)
            error_embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=error_embed)

    @commands.command(name="removetimeout")
    @commands.has_permissions(moderate_members=True)
    async def remove_timeout(self, ctx, user_input: str = None):
        """Remove timeout from a member."""
        if not user_input:
            embed = discord.Embed(
                title="⚠️ Remove Timeout Command",
                description="Please mention a user or provide their ID.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        user = await self.resolve_user(ctx, user_input)
        if not user:
            embed = discord.Embed(
                title="❌ User Not Found",
                description="I cannot find this user. Please check the ID/mention and try again.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        member = ctx.guild.get_member(user.id)
        if not member:
            embed = discord.Embed(
                title="❌ User Not in Server",
                description="This user is not in the server.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        try:
            if not member.is_timed_out():
                embed = discord.Embed(
                    title="⚠️ Not Timed Out",
                    description=f"{member.mention} is not currently timed out.",
                    color=discord.Color.orange(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.set_footer(text=f"Requested by {ctx.author}")
                await ctx.send(embed=embed)
                return

            await member.timeout(None, reason="Timeout removed by moderator")
            embed = discord.Embed(
                title="⏰ Timeout Removed",
                description=f"Timeout has been removed from {member.mention}",
                color=discord.Color.brand_green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
            embed.set_footer(text=f"Timeout removed by {ctx.author}")
            await ctx.send(embed=embed)
            
            log_embed = discord.Embed(
                title="⏰ Timeout Removed",
                description=f"Timeout has been removed from {user.mention}",
                color=discord.Color.yellow(),
                timestamp=datetime.now(timezone.utc)
            )
            log_embed.add_field(name="User", value=f"{user}", inline=True)
            log_embed.add_field(name="Moderator", value=f"{ctx.author}", inline=True)
            await self.log_action(ctx.guild, log_embed)
            
            try:
                dm_embed = discord.Embed(
                    title="Timeout Removed",
                    description=f"Your timeout in **{ctx.guild.name}** has been removed.",
                    color=discord.Color.brand_green(),
                    timestamp=datetime.now(timezone.utc)
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Remove Timeout Failed",
                description="An error occurred while trying to remove the timeout.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            error_embed.add_field(name="Error Details", value=str(e), inline=False)
            error_embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=error_embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True, manage_channels=True)
    async def createmuterole(self, ctx, role_name: str = "Muted"):
        """Create a mute role and set appropriate permissions."""
        guild = ctx.guild
        existing_role = discord.utils.get(guild.roles, name=role_name)
        
        if existing_role:
            embed = discord.Embed(
                title="⚠️ Role Already Exists",
                description=f"Role **{role_name}** is already set up in this server.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        progress_embed = discord.Embed(
            title="🔄 Creating Mute Role",
            description="Setting up role and configuring permissions...",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        progress_msg = await ctx.send(embed=progress_embed)

        try:
            mute_role = await guild.create_role(
                name=role_name,
                color=discord.Color.red(),  # Added red color
                reason=f"Mute role created by {ctx.author}"
            )
            
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

            success_embed = discord.Embed(
                title="✅ Mute Role Created",
                description=f"Role **{mute_role.name}** has been created and configured.",
                color=discord.Color.brand_green(),
                timestamp=datetime.now(timezone.utc)
            )
            success_embed.add_field(name="Role", value=mute_role.mention, inline=True)
            success_embed.add_field(name="Channels Updated", value=str(channels_updated), inline=True)
            success_embed.add_field(name="Categories Updated", value=str(categories_updated), inline=True)
            success_embed.set_footer(text=f"Created by {ctx.author}")
            
            await progress_msg.edit(embed=success_embed)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Role Creation Failed",
                description="An error occurred while setting up the mute role.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            error_embed.add_field(name="Error Details", value=str(e), inline=False)
            error_embed.set_footer(text=f"Requested by {ctx.author}")
            await progress_msg.edit(embed=error_embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setmuterole(self, ctx, role: discord.Role):
        """Set a custom mute role for the guild."""
        try:
            guild_id = str(ctx.guild.id)
            self.mute_roles[guild_id] = str(role.id)
            self.save_mute_roles()

            embed = discord.Embed(
                title="✅ Mute Role Set",
                description=f"Role {role.mention} has been set as the mute role.",
                color=discord.Color.brand_green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Role Name", value=role.name, inline=True)
            embed.add_field(name="Role ID", value=role.id, inline=True)
            embed.add_field(name="Color", value=f"#{str(role.color)[1:]}", inline=True)
            embed.add_field(name="Position", value=role.position, inline=True)
            embed.set_footer(text=f"Set by {ctx.author}")
            
            await ctx.send(embed=embed)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Setting Mute Role Failed",
                description="An error occurred while setting the mute role.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            error_embed.add_field(name="Error Details", value=str(e), inline=False)
            error_embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=error_embed)


    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, user_input: str = None, *, reason_or_duration: str = None):
        """Mute a member by mention or User ID."""
        if not user_input:
            embed = discord.Embed(
                title="⚠️ Mute Command",
                description="Please mention a user or provide a valid User ID.\nExample: `!mute @user [duration] [reason]`",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Duration Format", value="Use: s (seconds), m (minutes), h (hours), d (days)\nExample: 1h30m", inline=False)
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return
        duration = None
        reason = None
        if reason_or_duration:
            # Split the first word to check if it's a duration
            parts = reason_or_duration.split(maxsplit=1)
            first_word = parts[0]
            
            # Check if the first word matches duration pattern
            if re.match(r'^\d+[smhd](?:\d+[smhd])*$', first_word):
                duration = first_word
                reason = parts[1] if len(parts) > 1 else None
            else:
                # If first word isn't a duration, treat entire string as reason
                reason = reason_or_duration
    
        guild_id = str(ctx.guild.id)
        mute_role_id = self.mute_roles.get(guild_id)
        if not mute_role_id:
            embed = discord.Embed(
                title="❌ No Mute Role Set",
                description="No mute role configured! Use `!createmuterole` or `!setmuterole` first.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        mute_role = ctx.guild.get_role(int(mute_role_id))
        if not mute_role:
            embed = discord.Embed(
                title="❌ Mute Role Not Found",
                description="The configured mute role no longer exists. Please set up a new one.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        user = await self.resolve_user(ctx, user_input)
        if not user:
            embed = discord.Embed(
                title="❌ User Not Found",
                description="I cannot find this user. Please check the ID/mention and try again.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        member = ctx.guild.get_member(user.id)
        if not member:
            embed = discord.Embed(
                title="❌ User Not in Server",
                description="This user is not in the server.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        if mute_role in member.roles:
            embed = discord.Embed(
                title="⚠️ Already Muted",
                description=f"{member.mention} is already muted.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        try:
            await member.add_roles(mute_role, reason=reason)
            
            embed = discord.Embed(
                title="🔇 Member Muted",
                description=f"{member.mention} has been muted.",
                color=discord.Color.brand_green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
            if duration:
                embed.add_field(name="Duration", value=duration, inline=True)
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Muted by {ctx.author}")
            await ctx.send(embed=embed)
            
            # Track muted users
            if duration:
                total_seconds = self.parse_duration(duration)
                expiry = int((datetime.now(timezone.utc) + timedelta(seconds=total_seconds)).timestamp())
            else:
                expiry = 0  # 0 means indefinite

            guild_id = str(ctx.guild.id)
            if guild_id not in self.muted_users:
                self.muted_users[guild_id] = {}
            self.muted_users[guild_id][str(member.id)] = expiry
            self.save_muted_users()
            
            log_embed = discord.Embed(
                title="🔇 Member Muted",
                description=f"{user.mention} has been muted.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            log_embed.add_field(name="User", value=f"{user}", inline=True)
            log_embed.add_field(name="Moderator", value=f"{ctx.author}", inline=True)
            if duration:
                log_embed.add_field(name="Duration", value=duration, inline=True)
            if reason:
                log_embed.add_field(name="Reason", value=reason, inline=False)
            await self.log_action(ctx.guild, log_embed)
            try:
                dm_embed = discord.Embed(
                    title="You Have Been Muted",
                    description=f"You have been muted in **{ctx.guild.name}**",
                    color=discord.Color.red(),
                    timestamp=datetime.now(timezone.utc)
                )
                if duration:
                    dm_embed.add_field(name="Duration", value=duration, inline=True)
                if reason:
                    dm_embed.add_field(name="Reason", value=reason, inline=False)
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass

            if duration:
                total_seconds = self.parse_duration(duration)
                if total_seconds:
                    await asyncio.sleep(total_seconds)
                    if mute_role in member.roles:  # Check if still muted
                        await member.remove_roles(mute_role, reason="Mute duration expired")
                        unmute_embed = discord.Embed(
                            title="🔊 Member Unmuted",
                            description=f"{member.mention} has been automatically unmuted.",
                            color=discord.Color.brand_green(),
                            timestamp=datetime.now(timezone.utc)
                        )
                        unmute_embed.set_footer(text="Automatic unmute after duration expired")
                        await ctx.send(embed=unmute_embed)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Seems like something went wrong...",
                description="An error occurred while trying to mute the user.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            error_embed.add_field(name="Error Details", value=str(e), inline=False)
            error_embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=error_embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, user_input: str = None):
        """Unmute a member."""
        if not user_input:
            embed = discord.Embed(
                title="⚠️ Unmute Command",
                description="Please mention a user or provide a valid User ID.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        guild_id = str(ctx.guild.id)
        mute_role_id = self.mute_roles.get(guild_id)
        if not mute_role_id:
            embed = discord.Embed(
                title="❌ No Mute Role Set",
                description="No mute role configured! Use `createmuterole` or `setmuterole` first.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        mute_role = ctx.guild.get_role(int(mute_role_id))
        if not mute_role:
            embed = discord.Embed(
                title="❌ Mute Role Not Found",
                description="The configured mute role no longer exists. Please set up a new one.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        user = await self.resolve_user(ctx, user_input)
        if not user:
            embed = discord.Embed(
                title="❌ User Not Found",
                description="I cannot find this user. Please check the ID/mention and try again.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        member = ctx.guild.get_member(user.id)
        if not member:
            embed = discord.Embed(
                title="❌ User Not in Server",
                description="This user is not in the server.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        if mute_role not in member.roles:
            embed = discord.Embed(
                title="⚠️ Not Muted",
                description=f"{member.mention} is not muted.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        try:
            await member.remove_roles(mute_role, reason="Unmuted by moderator")
            embed = discord.Embed(
                title="🔊 Member Unmuted",
                description=f"{member.mention} has been unmuted.",
                color=discord.Color.brand_green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="User", value=f"{member} ({member.id})", inline=False)
            embed.set_footer(text=f"Unmuted by {ctx.author}")
            await ctx.send(embed=embed)
            
            # Remove the user from the muted_users dictionary
            guild_id = str(ctx.guild.id)
            if guild_id in self.muted_users:
                if str(member.id) in self.muted_users[guild_id]:
                    del self.muted_users[guild_id][str(member.id)]
                    self.save_muted_users()
                    
        
            log_embed = discord.Embed(
                title="🔊 Member Unmuted",
                description=f"{user.mention} has been unmuted",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            log_embed.add_field(name="User", value=f"{user}", inline=True)
            log_embed.add_field(name="Moderator", value=f"{ctx.author}", inline=True)
            await self.log_action(ctx.guild, log_embed)

            try:
                dm_embed = discord.Embed(
                    title="You Have Been Unmuted",
                    description=f"You have been unmuted in **{ctx.guild.name}**",
                    color=discord.Color.brand_green(),
                    timestamp=datetime.now(timezone.utc)
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Unmute Failed",
                description="An error occurred while trying to unmute the user.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            error_embed.add_field(name="Error Details", value=str(e), inline=False)
            error_embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=error_embed)


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlogchannel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel for moderation logs."""
        if not channel:
            channel = ctx.channel

        try:
            # Test permissions
            await channel.send(embed=discord.Embed(
                title="🔍 Permission Test",
                description="Testing bot permissions in this channel...",
                color=discord.Color.blue()
            ), delete_after=5)

            # Save the channel
            self.log_channels[str(ctx.guild.id)] = str(channel.id)
            self.save_log_channels()

            embed = discord.Embed(
                title="✅ Log Channel Set",
                description=f"Moderation logs will now be sent to {channel.mention}",
                color=discord.Color.brand_green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Channel", value=channel.name, inline=True)
            embed.add_field(name="Channel ID", value=channel.id, inline=True)
            embed.set_footer(text=f"Set by {ctx.author}")
            
            await ctx.send(embed=embed)

            # Send test log
            log_embed = discord.Embed(
                title="📝 Log Channel Test",
                description="This channel has been set as the moderation log channel.",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            log_embed.set_footer(text=f"Set up by {ctx.author}")
            await channel.send(embed=log_embed)

        except discord.Forbidden:
            error_embed = discord.Embed(
                title="❌ Permission Error",
                description="I don't have permission to send messages in that channel.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=error_embed)
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Setup Failed",
                description="An error occurred while setting up the log channel.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            error_embed.add_field(name="Error Details", value=str(e), inline=False)
            await ctx.send(embed=error_embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removelogchannel(self, ctx):
        """Remove the moderation log channel configuration."""
        guild_id = str(ctx.guild.id)
        if guild_id in self.log_channels:
            del self.log_channels[guild_id]
            self.save_log_channels()
            
            embed = discord.Embed(
                title="✅ Log Channel Removed",
                description="Moderation logs have been disabled for this server.",
                color=discord.Color.brand_green(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Removed by {ctx.author}")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="⚠️ No Log Channel",
                description="No log channel was configured for this server.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount='10'):
        """Clear a specified number of messages from the channel."""
        try:
            if amount.lower() == 'all':
                progress_embed = discord.Embed(
                    title="🔄 Clearing Messages",
                    description="Clearing all messages in this channel...",
                    color=discord.Color.blue(),
                    timestamp=datetime.now(timezone.utc)
                )
                progress_msg = await ctx.send(embed=progress_embed)
                
                deleted = await ctx.channel.purge(limit=None, check=lambda m: m.id != progress_msg.id)
                
                success_embed = discord.Embed(
                    title="🧹 Channel Cleared",
                    description=f"Successfully cleared {len(deleted)} messages.",
                    color=discord.Color.brand_green(),
                    timestamp=datetime.now(timezone.utc)
                )
                success_embed.set_footer(text=f"Cleared by {ctx.author}")
                await progress_msg.edit(embed=success_embed)
                await asyncio.sleep(5)
                await progress_msg.delete()
                
            else:
                amount = int(amount)
                if amount < 1:
                    raise ValueError("Amount must be at least 1")
                    
                progress_embed = discord.Embed(
                    title="🔄 Clearing Messages",
                    description=f"Clearing {amount} messages...",
                    color=discord.Color.blue(),
                    timestamp=datetime.now(timezone.utc)
                )
                progress_msg = await ctx.send(embed=progress_embed)
                
                deleted = await ctx.channel.purge(limit=amount + 1, check=lambda m: m.id != progress_msg.id)
                
                success_embed = discord.Embed(
                    title="🧹 Messages Cleared",
                    description=f"Successfully cleared {len(deleted) - 1} messages.",
                    color=discord.Color.brand_green(),
                    timestamp=datetime.now(timezone.utc)
                )
                success_embed.set_footer(text=f"Cleared by {ctx.author}")
                await progress_msg.edit(embed=success_embed)
                await asyncio.sleep(5)
                await progress_msg.delete()

        except ValueError:
            embed = discord.Embed(
                title="⚠️ Invalid Input",
                description="Please provide a valid number or 'all'.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed, delete_after=5)
            
        except discord.HTTPException as e:
            if e.code == 50034:
                embed = discord.Embed(
                    title="⚠️ Age Limit Reached",
                    description="Cannot delete messages older than 14 days.",
                    color=discord.Color.orange(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.set_footer(text=f"Requested by {ctx.author}")
                await ctx.send(embed=embed, delete_after=5)
            else:
                raise
                
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Clear Failed",
                description="An error occurred while clearing messages.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            error_embed.add_field(name="Error Details", value=str(e), inline=False)
            error_embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=error_embed, delete_after=5)


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="Permission Denied",
                description="You don't have permission to use this command.",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Check if joining member should be muted."""
        guild_id = str(member.guild.id)
        user_id = str(member.id)
        
        if guild_id in self.muted_users and user_id in self.muted_users[guild_id]:
            expiry = self.muted_users[guild_id][user_id]
            current_time = int(datetime.now(timezone.utc).timestamp())
            
            # Check if mute has expired
            if expiry != 0 and current_time > expiry:
                # Mute has expired, remove from tracking
                del self.muted_users[guild_id][user_id]
                self.save_muted_users()
                return
                
            # Reapply mute role
            mute_role_id = self.mute_roles.get(guild_id)
            if mute_role_id:
                mute_role = member.guild.get_role(int(mute_role_id))
                if mute_role:
                    try:
                        await member.add_roles(mute_role, reason="Mute evasion prevention")
                        
                        # Log the action
                        log_embed = discord.Embed(
                            title="🔇 Mute Reapplied",
                            description=f"Mute role reapplied to {member.mention} upon rejoining",
                            color=discord.Color.red(),
                            timestamp=datetime.now(timezone.utc)
                        )
                        log_embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
                        log_embed.add_field(name="Reason", value="Mute evasion prevention", inline=True)
                        if expiry:
                            log_embed.add_field(
                                name="Expires", 
                                value=f"<t:{expiry}:R>", 
                                inline=True
                            )
                        await self.log_action(member.guild, log_embed)
                        
                    except Exception:
                        logger.exception(f"Failed to reapply mute role to {member}")


    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Log when a muted member leaves the server."""
        guild_id = str(member.guild.id)
        user_id = str(member.id)
        
        if guild_id in self.muted_users and user_id in self.muted_users[guild_id]:
            log_embed = discord.Embed(
                title="⚠️ Muted Member Left",
                description=f"A muted member ({member.mention}) has left the server",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            log_embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
            log_embed.set_footer(text="Member will be re-muted if they rejoin")
            await self.log_action(member.guild, log_embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
