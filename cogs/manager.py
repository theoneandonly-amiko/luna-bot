import discord
from discord.ext import commands
from discord.utils import get
from collections import defaultdict
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)

class Manager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "cogs/data/auditlog_config.json"
        self.config_data = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
            self.save_config(data)
            return data

    def save_config(self, data):
        with open(self.config_file, "w") as file:
            json.dump(data, file, indent=4)

    def get_audit_log_channel(self, guild_id):
        guild_config = self.config_data.get(str(guild_id), {})
        return guild_config.get("log_channel")

    def set_audit_log_channel(self, guild_id, channel_id):
        guild_config = self.config_data.setdefault(str(guild_id), {})
        guild_config["log_channel"] = channel_id
        self.save_config(self.config_data)

    def create_error_embed(self, title: str, description: str):
        """Create a standardized error embed."""
        return discord.Embed(
            title=title,
            description=description,
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )

    # Role management commands
    @commands.command(name="addrole")
    @commands.has_permissions(manage_roles=True)
    async def add_role(self, ctx, member: discord.Member = None, role: discord.Role = None):
        """Assigns a role to a specified user."""
        if not member or not role:
            embed = self.create_error_embed("Missing Parameters", "Please specify both a member and a role.")
            await ctx.send(embed=embed)
            return
        try:
            if role in member.roles:
                embed = discord.Embed(
                    description=f"{member.mention} already has the {role.mention} role.",
                    color=discord.Color.orange(),
                    timestamp=datetime.now(timezone.utc)
                )
                await ctx.send(embed=embed)
            else:
                await member.add_roles(role)
                embed = discord.Embed(
                    description=f"Added {role.mention} role to {member.mention}.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = self.create_error_embed("Permission Error", "I don't have permission to manage roles.")
            await ctx.send(embed=embed)
        except Exception as e:
            logger.exception("Failed to add role:")
            embed = self.create_error_embed("Error Adding Role", f"An error occurred: {e}")
            await ctx.send(embed=embed)

    @commands.command(name="removerole")
    @commands.has_permissions(manage_roles=True)
    async def remove_role(self, ctx, member: discord.Member = None, role: discord.Role = None):
        """Removes a role from a specified user."""
        if not member or not role:
            embed = self.create_error_embed("Missing Parameters", "Please specify both a member and a role.")
            await ctx.send(embed=embed)
            return
        try:
            if role not in member.roles:
                embed = discord.Embed(
                    description=f"{member.mention} does not have the {role.mention} role.",
                    color=discord.Color.orange(),
                    timestamp=datetime.now(timezone.utc)
                )
                await ctx.send(embed=embed)
            else:
                await member.remove_roles(role)
                embed = discord.Embed(
                    description=f"Removed {role.mention} role from {member.mention}.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = self.create_error_embed("Permission Error", "I don't have permission to manage roles.")
            await ctx.send(embed=embed)
        except Exception as e:
            logger.exception("Failed to remove role:")
            embed = self.create_error_embed("Error Removing Role", f"An error occurred: {e}")
            await ctx.send(embed=embed)

    @commands.command(name="createrole")
    @commands.has_permissions(manage_roles=True)
    async def create_role(self, ctx, role_name: str = None, color_hex: str = None):
        """Creates a new role with optional color (hex code)."""
        if not role_name:
            embed = self.create_error_embed("Missing Role Name", "Please provide a name for the new role.")
            await ctx.send(embed=embed)
            return

        guild = ctx.guild
        existing_role = discord.utils.get(guild.roles, name=role_name)
        if existing_role:
            embed = self.create_error_embed("Role Already Exists", f"A role named '{role_name}' already exists.")
            await ctx.send(embed=embed)
            return

        color = discord.Color.default()
        if color_hex:
            try:
                color = discord.Color(int(color_hex.strip("#"), 16))
            except ValueError:
                embed = self.create_error_embed("Invalid Color Code", "Please provide a valid hex color code, e.g., `#ff5733`.")
                await ctx.send(embed=embed)
                return

        try:
            new_role = await guild.create_role(name=role_name, color=color)
            embed = discord.Embed(
                description=f"Created role {new_role.mention} with color `{color_hex or 'default'}`.",
                color=color,
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = self.create_error_embed("Permission Error", "I don't have permission to create roles.")
            await ctx.send(embed=embed)
        except Exception as e:
            logger.exception("Failed to create role:")
            embed = self.create_error_embed("Error Creating Role", f"An error occurred: {e}")
            await ctx.send(embed=embed)

    @commands.command(name="deleterole")
    @commands.has_permissions(manage_roles=True)
    async def delete_role(self, ctx, role: discord.Role = None):
        """Deletes a specified role."""
        if not role:
            embed = self.create_error_embed("Missing Role", "Please specify a role to delete.")
            await ctx.send(embed=embed)
            return
        try:
            await role.delete()
            embed = discord.Embed(
                description=f"Deleted the role '{role.name}'.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = self.create_error_embed("Permission Error", "I don't have permission to delete roles.")
            await ctx.send(embed=embed)
        except Exception as e:
            logger.exception("Failed to delete role:")
            embed = self.create_error_embed("Error Deleting Role", f"An error occurred: {e}")
            await ctx.send(embed=embed)

    @commands.command(name="listroles")
    async def list_roles(self, ctx):
        """Lists all roles in the server with the number of members in each, grouped by member count."""
        roles = ctx.guild.roles[1:]  # Skip @everyone role

        if not roles:
            embed = discord.Embed(
                description="No roles found in this server.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            return

        # Sort roles by member count
        roles.sort(key=lambda r: len(r.members), reverse=True)

        pages = []
        page = ""
        for role in roles:
            entry = f"{role.name}: {len(role.members)} members\n"
            if len(page) + len(entry) > 1024:
                pages.append(page)
                page = entry
            else:
                page += entry
        if page:
            pages.append(page)

        for index, content in enumerate(pages, start=1):
            embed = discord.Embed(
                title=f"Roles in {ctx.guild.name} (Page {index}/{len(pages)})",
                description=content,
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)

    # Channel management
    @commands.command(name="createchannel")
    @commands.has_permissions(manage_channels=True)
    async def create_channel(self, ctx, channel_name: str = None, channel_type: str = "text", *, category: discord.CategoryChannel = None):
        """Creates a new channel of specified type (text/voice/stage) and optional category."""
        if not channel_name:
            embed = self.create_error_embed("Missing Channel Name", "Please provide a name for the new channel.")
            await ctx.send(embed=embed)
            return

        channel_type = channel_type.lower()
        guild = ctx.guild

        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            embed = self.create_error_embed("Channel Already Exists", f"A channel named '{channel_name}' already exists.")
            await ctx.send(embed=embed)
            return

        try:
            if channel_type == "text":
                channel = await guild.create_text_channel(channel_name, category=category)
            elif channel_type == "voice":
                channel = await guild.create_voice_channel(channel_name, category=category)
            elif channel_type == "stage":
                channel = await guild.create_stage_channel(channel_name, category=category)
            else:
                embed = self.create_error_embed("Invalid Channel Type", "Please use `text`, `voice`, or `stage`.")
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(
                description=f"Created {channel_type} channel {channel.mention}.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = self.create_error_embed("Permission Error", "I don't have permission to create channels.")
            await ctx.send(embed=embed)
        except Exception as e:
            logger.exception("Failed to create channel:")
            embed = self.create_error_embed("Error Creating Channel", f"An error occurred: {e}")
            await ctx.send(embed=embed)

    @commands.command(name="createcategory")
    @commands.has_permissions(manage_channels=True)
    async def create_category(self, ctx, *, name: str = None):
        """Creates a new category with the specified name."""
        if not name:
            embed = self.create_error_embed("Missing Category Name", "Please provide a name for the new category.")
            await ctx.send(embed=embed)
            return

        guild = ctx.guild

        existing_category = discord.utils.get(guild.categories, name=name)
        if existing_category:
            embed = self.create_error_embed("Category Already Exists", f"A category named '{name}' already exists.")
            await ctx.send(embed=embed)
            return

        try:
            category = await guild.create_category(name=name)
            embed = discord.Embed(
                description=f"Category '{category.name}' has been created.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = self.create_error_embed("Permission Error", "I don't have permission to create categories.")
            await ctx.send(embed=embed)
        except Exception as e:
            logger.exception("Failed to create category:")
            embed = self.create_error_embed("Error Creating Category", f"An error occurred: {e}")
            await ctx.send(embed=embed)

    @commands.command(name="deletechannel")
    @commands.has_permissions(manage_channels=True)
    async def delete_channel(self, ctx, channel: discord.abc.GuildChannel = None):
        """Deletes a specified channel."""
        if not channel:
            embed = self.create_error_embed("Missing Channel", "Please mention a channel to delete.")
            await ctx.send(embed=embed)
            return

        try:
            channel_name = channel.name
            await channel.delete()
            embed = discord.Embed(
                description=f"Deleted channel '{channel_name}'.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = self.create_error_embed("Permission Error", "I don't have permission to delete channels.")
            await ctx.send(embed=embed)
        except Exception as e:
            logger.exception("Failed to delete channel:")
            embed = self.create_error_embed("Error Deleting Channel", f"An error occurred: {e}")
            await ctx.send(embed=embed)

    @commands.command(name="deletecategory")
    @commands.has_permissions(manage_channels=True)
    async def delete_category(self, ctx, *, name: str = None):
        """Deletes a category with the specified name."""
        if not name:
            embed = self.create_error_embed("Missing Category Name", "Please provide the name of the category to delete.")
            await ctx.send(embed=embed)
            return

        guild = ctx.guild

        category = discord.utils.get(guild.categories, name=name)
        if not category:
            embed = self.create_error_embed("Category Not Found", f"No category found with the name '{name}'.")
            await ctx.send(embed=embed)
            return

        try:
            await category.delete()
            embed = discord.Embed(
                description=f"Category '{name}' has been deleted.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = self.create_error_embed("Permission Error", "I don't have permission to delete categories.")
            await ctx.send(embed=embed)
        except Exception as e:
            logger.exception("Failed to delete category:")
            embed = self.create_error_embed("Error Deleting Category", f"An error occurred: {e}")
            await ctx.send(embed=embed)

    @commands.command(name="setchannelname")
    @commands.has_permissions(manage_channels=True)
    async def set_channel_name(self, ctx, channel: discord.abc.GuildChannel = None, *, new_name: str = None):
        """Changes the name of a specified channel."""
        if not channel or not new_name:
            embed = self.create_error_embed("Missing Parameters", "Please specify both a channel and a new name.")
            await ctx.send(embed=embed)
            return
        try:
            await channel.edit(name=new_name)
            embed = discord.Embed(
                description=f"Changed channel name to '{new_name}'.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = self.create_error_embed("Permission Error", "I don't have permission to manage channels.")
            await ctx.send(embed=embed)
        except Exception as e:
            logger.exception("Failed to set channel name:")
            embed = self.create_error_embed("Error Changing Channel Name", f"An error occurred: {e}")
            await ctx.send(embed=embed)

    @commands.command(name="setchannelcategory")
    @commands.has_permissions(manage_channels=True)
    async def set_channel_category(self, ctx, channel: discord.abc.GuildChannel = None, category: discord.CategoryChannel = None):
        """Moves a channel to a different category."""
        if not channel or not category:
            embed = self.create_error_embed("Missing Parameters", "Please specify both a channel and a category.")
            await ctx.send(embed=embed)
            return
        try:
            await channel.edit(category=category)
            embed = discord.Embed(
                description=f"Moved channel '{channel.name}' to category '{category.name}'.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = self.create_error_embed("Permission Error", "I don't have permission to manage channels.")
            await ctx.send(embed=embed)
        except Exception as e:
            logger.exception("Failed to set channel category:")
            embed = self.create_error_embed("Error Changing Channel Category", f"An error occurred: {e}")
            await ctx.send(embed=embed)

    @commands.command(name="listchannels")
    async def list_channels(self, ctx):
        """Lists all channels in the server, grouped by categories."""
        guild = ctx.guild

        # Categorize channels
        categorized_channels = defaultdict(list)
        uncategorized_channels = []

        for channel in guild.channels:
            if channel.category:
                categorized_channels[channel.category.name].append(channel)
            else:
                uncategorized_channels.append(channel)

        embed = discord.Embed(
            title=f"Channels in {guild.name}",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )

        # Add categorized channels to embed
        for category_name, channels in categorized_channels.items():
            channel_list = "\n".join([f"{channel.name} ({channel.type.name.capitalize()})" for channel in channels])
            if len(channel_list) > 1024:
                # Split into multiple fields if necessary
                channel_chunks = [channel_list[i:i+1024] for i in range(0, len(channel_list), 1024)]
                for idx, chunk in enumerate(channel_chunks):
                    field_name = f"{category_name} (Part {idx+1})" if idx > 0 else category_name
                    embed.add_field(name=field_name, value=chunk, inline=False)
            else:
                embed.add_field(name=category_name, value=channel_list, inline=False)

        # Add uncategorized channels to embed
        if uncategorized_channels:
            uncategorized_list = "\n".join([f"{channel.name} ({channel.type.name.capitalize()})" for channel in uncategorized_channels])
            embed.add_field(name="Uncategorized Channels", value=uncategorized_list, inline=False)

        await ctx.send(embed=embed)

    # Server settings
    @commands.command(name="viewsettings")
    @commands.has_permissions(administrator=True)
    async def view_settings(self, ctx):
        """View the current server settings as an embed."""
        guild = ctx.guild
        verification_level = guild.verification_level
        embed = discord.Embed(
            title=f"Server Settings for {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Verification Level", value=verification_level.name.capitalize(), inline=False)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await ctx.send(embed=embed)

    @commands.command(name="setservername")
    @commands.has_permissions(manage_guild=True)
    async def set_server_name(self, ctx, *, name: str = None):
        """Change the server's name."""
        if not name:
            embed = self.create_error_embed("Missing Server Name", "Please provide a new name for the server.")
            await ctx.send(embed=embed)
            return
        old_name = ctx.guild.name
        try:
            await ctx.guild.edit(name=name)
            embed = discord.Embed(
                description=f"Server name changed from '{old_name}' to '{name}'.",
                color=discord.Color.green(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = self.create_error_embed("Permission Error", "I don't have permission to change the server name.")
            await ctx.send(embed=embed)
        except Exception as e:
            logger.exception("Failed to set server name:")
            embed = self.create_error_embed("Error Changing Server Name", f"An error occurred: {e}")
            await ctx.send(embed=embed)

    @commands.command(name="setverificationlevel")
    @commands.has_permissions(administrator=True)
    async def set_verification_level(self, ctx, level: int = None):
        """Set server verification level (0-4)."""
        if level is None:
            embed = self.create_error_embed("Missing Level", "Please provide a verification level from 0 (None) to 4 (Highest).")
            await ctx.send(embed=embed)
            return
        levels = [
            discord.VerificationLevel.none, 
            discord.VerificationLevel.low,
            discord.VerificationLevel.medium, 
            discord.VerificationLevel.high,
            discord.VerificationLevel.highest
        ]
        if 0 <= level < len(levels):
            try:
                await ctx.guild.edit(verification_level=levels[level])
                embed = discord.Embed(
                    description=f"Verification level set to {levels[level].name.capitalize().replace('_', ' ')}.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                await ctx.send(embed=embed)
            except discord.Forbidden:
                embed = self.create_error_embed("Permission Error", "I don't have permission to change the verification level.")
                await ctx.send(embed=embed)
            except Exception as e:
                logger.exception("Failed to set verification level:")
                embed = self.create_error_embed("Error Changing Verification Level", f"An error occurred: {e}")
                await ctx.send(embed=embed)
        else:
            embed = self.create_error_embed("Invalid Level", "Use a number from 0 (None) to 4 (Very High).")
            await ctx.send(embed=embed)

    # List bans in a guild
    @commands.command(name="listbans")
    @commands.has_permissions(ban_members=True)
    async def list_bans(self, ctx):
        """Lists all banned users in the server."""
        try:
            ban_entries = []
            async for ban_entry in ctx.guild.bans():
                ban_entries.append(ban_entry)

            if not ban_entries:
                embed = discord.Embed(
                    description="There are no banned users in this server.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                await ctx.send(embed=embed)
                return

            embeds = []
            embed = discord.Embed(
                title=f"Banned Users in {ctx.guild.name}",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )

            for index, ban_entry in enumerate(ban_entries, start=1):
                user = ban_entry.user
                embed.add_field(
                    name=f"{user.name}",
                    value=f"ID: {user.id}",
                    inline=False
                )
                if len(embed.fields) == 25 or index == len(ban_entries):
                    embeds.append(embed)
                    if index < len(ban_entries):
                        embed = discord.Embed(
                            title=f"Banned Users in {ctx.guild.name} (cont.)",
                            color=discord.Color.red(),
                            timestamp=datetime.now(timezone.utc)
                        )

            for e in embeds:
                await ctx.send(embed=e)

        except Exception as e:
            logger.exception("Failed to list bans:")
            embed = self.create_error_embed("Error Listing Bans", f"An error occurred: {e}")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Manager(bot))