import discord
from discord.ext import commands
from discord.utils import get
from collections import defaultdict
import json


class Manager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel = None
        self.audit_logging_enabled = False
        self.config_file = "cogs/data/auditlog_config.json"
        self.audit_log_channel = self.load_audit_log_channel()
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, "r") as file:
                data = json.load(file)
                self.log_channel = data.get("log_channel")
                self.audit_logging_enabled = data.get("audit_logging_enabled", False)
        except FileNotFoundError:
            # Config file doesn't exist, create an empty one
            self.save_config()

    def save_config(self):
        with open(self.config_file, "w") as file:
            json.dump({
                "log_channel": self.log_channel,
                "audit_logging_enabled": self.audit_logging_enabled
            }, file)

    def load_audit_log_channel(self):
        """Loads the audit log channel ID from the JSON file."""
        try:
            with open(self.config_file, "r") as file:
                data = json.load(file)
                return data.get("log_channel")
        except FileNotFoundError:
            return None

    def get_audit_log_channel(self, guild_id):
        """Gets the audit log channel for a specific guild from the JSON file."""
        try:
            with open(self.config_file, "r") as file:
                data = json.load(file)
                return data.get(str(guild_id), {}).get("log_channel")
        except FileNotFoundError:
            return None

    def set_audit_log_channel(self, guild_id, channel_id):
        """Sets the audit log channel for a specific guild in the JSON file."""
        try:
            with open(self.config_file, "r") as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}

        data[str(guild_id)] = {"log_channel": channel_id}

        with open(self.config_file, "w") as file:
            json.dump(data, file, indent=4)



    @commands.command(name="addrole")
    @commands.has_permissions(manage_roles=True)
    async def add_role(self, ctx, member: discord.Member, role: discord.Role):
        """Assigns a role to a specified user."""
        if role in member.roles:
            await ctx.send(f"{member.mention} already has the {role.name} role.")
        else:
            await member.add_roles(role)
            await ctx.send(f"Added {role.mention} role to {member.mention}.")

    @commands.command(name="removerole")
    @commands.has_permissions(manage_roles=True)
    async def remove_role(self, ctx, member: discord.Member, role: discord.Role):
        """Removes a role from a specified user."""
        if role not in member.roles:
            await ctx.send(f"{member.mention} does not have the {role.name} role.")
        else:
            await member.remove_roles(role)
            await ctx.send(f"Removed {role.mention} role from {member.mention}.")

    @commands.command(name="createrole")
    @commands.has_permissions(manage_roles=True)
    async def create_role(self, ctx, role_name: str, color_hex: str = None):
        """Creates a new role with optional color (hex code)."""
        guild = ctx.guild

        # Set default color if no color hex is provided
        color = discord.Color.default()
        
        if color_hex:
            # Convert hex code to Discord color object, strip '#' if present
            try:
                color = discord.Color(int(color_hex.lstrip("#"), 16))
            except ValueError:
                await ctx.send("Invalid color hex code. Please use a valid hex format, e.g., #ff5733.")
                return

        await guild.create_role(name=role_name, color=color)
        await ctx.send(f"Created role '{role_name}' with color `{color_hex or 'default'}`.")

    @commands.command(name="deleterole")
    @commands.has_permissions(manage_roles=True)
    async def delete_role(self, ctx, role: discord.Role):
        """Deletes a specified role."""
        await role.delete()
        await ctx.send(f"Deleted the role '{role.name}'.")

    @commands.command(name="listroles")
    async def list_roles(self, ctx):
        """Lists all roles in the server with the number of members in each, grouped by member count."""
        roles = ctx.guild.roles[1:]  # Skip @everyone role

        # Group roles by member count
        role_groups = defaultdict(list)
        for role in roles:
            member_count = len(role.members)
            if member_count > 0:
                role_groups[member_count].append(role.name)
        
        # Create embed
        embed = discord.Embed(
            title=f"Roles in {ctx.guild.name}",
            color=discord.Color.blue()
        )
        
        for member_count, role_names in sorted(role_groups.items(), reverse=True):
            role_list = ", ".join(role_names)
            embed.add_field(name=f"{member_count} members", value=role_list, inline=False)

        await ctx.send(embed=embed)
        
# channel management
    @commands.command(name="createchannel")
    @commands.has_permissions(manage_channels=True)
    async def create_channel(self, ctx, channel_name: str, channel_type: str = "text", *, category: discord.CategoryChannel = None):
        """Creates a new channel of specified type (text/voice/stage) and optional category."""
        channel_type = channel_type.lower()
        
        if channel_type == "text":
            channel = await ctx.guild.create_text_channel(channel_name, category=category)
        elif channel_type == "voice":
            channel = await ctx.guild.create_voice_channel(channel_name, category=category)
        elif channel_type == "stage":
            channel = await ctx.guild.create_stage_channel(channel_name, category=category)
        else:
            await ctx.send("Invalid channel type! Please use `text`, `voice` or `stage`.")
            return
        
        await ctx.send(f"Created {channel_type} channel '{channel.name}'.")

    @commands.command(name="createcategory")
    @commands.has_permissions(manage_channels=True)
    async def create_category(self, ctx, *, name: str):
        """Creates a new category with the specified name."""
        guild = ctx.guild
        
        # Check if a category with the same name already exists
        existing_category = discord.utils.get(guild.categories, name=name)
        if existing_category:
            await ctx.send(f"A category with the name '{name}' already exists.")
            return
        
        # Create the category
        category = await guild.create_category(name=name)
        await ctx.send(f"Category '{category.name}' has been created.")

    @commands.command(name="deletechannel")
    @commands.has_permissions(manage_channels=True)
    async def delete_channel(self, ctx, channel: discord.abc.GuildChannel):
        """Deletes a specified channel."""
        await channel.delete()
        await ctx.send(f"Deleted channel '{channel.name}'.")

    @commands.command(name="deletecategory")
    @commands.has_permissions(manage_channels=True)
    async def delete_category(self, ctx, *, name: str):
        """Deletes a category with the specified name."""
        guild = ctx.guild
        
        # Find the category with the specified name
        category = discord.utils.get(guild.categories, name=name)
        if not category:
            await ctx.send(f"No category found with the name '{name}'.")
            return
        
        # Delete the category
        await category.delete()
        await ctx.send(f"Category '{name}' has been deleted.")


    @commands.command(name="setchannelname")
    @commands.has_permissions(manage_channels=True)
    async def set_channel_name(self, ctx, channel: discord.abc.GuildChannel, *, new_name: str):
        """Changes the name of a specified channel."""
        await channel.edit(name=new_name)
        await ctx.send(f"Changed channel name to '{new_name}'.")

    @commands.command(name="setchannelcategory")
    @commands.has_permissions(manage_channels=True)
    async def set_channel_category(self, ctx, channel: discord.abc.GuildChannel, category: discord.CategoryChannel):
        """Moves a channel to a different category."""
        await channel.edit(category=category)
        await ctx.send(f"Moved channel '{channel.name}' to category '{category.name}'.")

    @commands.command(name="listchannels")
    async def list_channels(self, ctx):
        """Lists all channels in the server, grouped by categories."""
        
        # Categorize channels
        categorized_channels = defaultdict(list)
        uncategorized_channels = []

        for channel in ctx.guild.text_channels + ctx.guild.voice_channels + ctx.guild.stage_channels:
            if channel.category:
                categorized_channels[channel.category.name].append(channel)
            else:
                uncategorized_channels.append(channel)
        
        # Create embed
        embed = discord.Embed(
            title=f"Channels in {ctx.guild.name}",
            color=discord.Color.green()
        )

        # Add categorized channels to embed
        for category_name, channels in categorized_channels.items():
            channel_list = "\n".join([f"{channel.name} ({channel.type.name.capitalize()})" for channel in channels])
            embed.add_field(name=category_name, value=channel_list)
        
        # Add uncategorized channels to embed
        if uncategorized_channels:
            uncategorized_list = "\n".join([f"{channel.name} ({channel.type.name.capitalize()})" for channel in uncategorized_channels])
            embed.add_field(name="Uncategorized Channels", value=uncategorized_list)

        await ctx.send(embed=embed)

# Server setting
    @commands.command(name="viewsettings")
    @commands.has_permissions(administrator=True)
    async def view_settings(self, ctx):
        """View the current server settings as an embed."""
        guild = ctx.guild
        verification_level = guild.verification_level
        audit_log_channel = self.bot.get_channel(self.audit_log_channel)

        embed = discord.Embed(
            title=f"Server Settings for {guild.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Verification Level", value=verification_level.name, inline=False)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

        await ctx.send(embed=embed)

    @commands.command(name="setservername")
    @commands.has_permissions(manage_guild=True)
    async def set_server_name(self, ctx, *, name: str):
        """Change the server's name."""
        old_name = ctx.guild.name
        await ctx.guild.edit(name=name)
        await ctx.send(f"Server name changed from '{old_name}' to '{name}'.")

    @commands.command(name="setverificationlevel")
    @commands.has_permissions(administrator=True)
    async def set_verification_level(self, ctx, level: int):
        """Set server verification level (0-4)."""
        levels = [
            discord.VerificationLevel.none, 
            discord.VerificationLevel.low,
            discord.VerificationLevel.medium, 
            discord.VerificationLevel.high,
            discord.VerificationLevel.highest
        ]
        if 0 <= level < len(levels):
            await ctx.guild.edit(verification_level=levels[level])
            await ctx.send(f"Verification level set to {levels[level].name.replace('_', ' ').title()}.")
        else:
            await ctx.send("Invalid level! Use a number from 0 (None) to 4 (Very High).")


# List bans in a guild
    @commands.command(name="listbans")
    @commands.has_permissions(ban_members=True)
    async def list_bans(self, ctx):
        """Lists all banned users in the server."""
        bans = []
        async for ban_entry in ctx.guild.bans():
            bans.append(ban_entry)
        
        if not bans:
            await ctx.send("There are no banned users in this server.")
            return
        
        embed_list = []
        embed = discord.Embed(
            title=f"Banned Users in {ctx.guild.name}",
            color=discord.Color.red()
        )

        for index, ban_entry in enumerate(bans, start=1):
            user = ban_entry.user
            embed.add_field(name=user.name, value=f"ID: {user.id}")
            
            # Check if embed fields are at limit or if it's the last user
            if len(embed.fields) == 25 or index == len(bans):
                embed_list.append(embed)
                if index < len(bans):  # Prepare a new embed if there are more users left
                    embed = discord.Embed(
                        title=f"Banned Users in {ctx.guild.name} (cont.)",
                        color=discord.Color.red()
                    )
        
        for e in embed_list:
            await ctx.send(embed=e)




async def setup(bot):
    await bot.add_cog(Manager(bot))