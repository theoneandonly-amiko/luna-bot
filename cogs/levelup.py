import discord
import aiofiles
import shutil
import aiohttp
import random
import os
import aiosqlite
import json
import asyncio
import logging

from typing import Union
from io import BytesIO
from discord.ext import commands, tasks
from discord.ext.commands import cooldown, BucketType
from PIL import Image, ImageDraw, ImageFont
from .database.db_manager import LevelDatabase
from .database.schema import init_db
from datetime import datetime, timedelta, timezone
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot       
        self.db = LevelDatabase()
        self.last_message_time = {}

        # Keep these for migration purposes
        self.levels_file = 'cogs/data/levels.json'
        self.roles_file = 'cogs/data/roles.json'
        self.config_file = 'cogs/data/level_config.json'
        self.block_guild_file = 'cogs/data/blocked_guilds.json'
        

        self.progress_bar_styles = [
            ("█", "░"),  # Style 1
            ("▓", "░"),  # Style 2
            ("■", "□"),  # Style 3
            ("▮", "▯"),  # Style 4
            ("⬜", "⬛"), # Style 5
            ("🟦", "⬜"), # Style 66
            ]

    async def cog_load(self):
        """Initialize the cog by loading data asynchronously."""
        await init_db()
        await self.migrate_json_to_db()  # Only run this once
        
    def cog_unload(self):
        """Cleanup when the cog is unloaded."""
        pass

    async def migrate_json_to_db(self):
        """Migrate all existing JSON data to SQLite database"""
        # Migrate levels
        if os.path.exists(self.levels_file):
            async with aiofiles.open(self.levels_file, 'r') as f:
                levels_data = json.loads(await f.read())
                for guild_id, users in levels_data.items():
                    for user_id, data in users.items():
                        await self.db.update_user_level(guild_id, user_id, data['xp'], data['level'])

        # Migrate roles
        if os.path.exists(self.roles_file):
            async with aiofiles.open(self.roles_file, 'r') as f:
                roles_data = json.loads(await f.read())
                for guild_id, guild_roles in roles_data.items():
                    await self.db.migrate_roles(guild_id, guild_roles)

        # Migrate config
        if os.path.exists(self.config_file):
            async with aiofiles.open(self.config_file, 'r') as f:
                config_data = json.loads(await f.read())
                for guild_id, guild_config in config_data.items():
                    await self.db.migrate_config(guild_id, guild_config)

        # Migrate blocked guild
        if os.path.exists(self.block_guild_file):
            async with aiofiles.open(self.block_guild_file, 'r') as f:
                config_data = json.loads(await f.read())
                for guild_id, guild_config in config_data.items():
                    await self.db.migrate_config(guild_id, guild_config)

        logger.info("Data migration completed successfully")


    async def is_user_restricted(self, guild_id: str, user_id: str) -> bool:
        """Check if a user is restricted from gaining XP."""
        async with aiosqlite.connect(self.db.db_path) as db:
            async with db.execute(
                'SELECT 1 FROM restricted_entities WHERE guild_id = ? AND entity_id = ? AND entity_type = ?',
                (guild_id, user_id, 'user')
            ) as cursor:
                return bool(await cursor.fetchone())

    async def can_receive_xp(self, guild_id: str, user_id: str) -> bool:
        """Check if enough time has passed to receive more XP."""
        now = datetime.now(timezone.utc)
        guild_config = await self.db.get_guild_config(guild_id)
        cooldown = guild_config.get('xp_cooldown', 10)  # Default 10 seconds
        
        last_time = self.last_message_time.get((guild_id, user_id))
        if last_time is None or (now - last_time).total_seconds() >= cooldown:
            self.last_message_time[(guild_id, user_id)] = now
            return True
        return False


    async def add_xp(self, guild_id, user_id, xp):
        """Add XP to a user and handle level-ups."""
        guild_id = str(guild_id)
        user_id = str(user_id)

        # Check if the guild is blocked
        guild_config = await self.db.get_guild_config(guild_id)
        if guild_config.get('is_blocked'):
            return False

        if await self.is_user_restricted(guild_id, user_id):
            return False

        leveled_up, new_level, current_xp = await self.db.add_xp(guild_id, user_id, xp)
        return leveled_up


    def xp_for_next_level(self, level):
        """Calculate the XP required for the next level."""
        return int(100 * (level ** 1.5))

    def create_progress_bar(self, current_xp, xp_needed, bar_length=20):
        """Generate a random custom ASCII progress bar for the level embed."""
        progress = int((current_xp / xp_needed) * bar_length)
        full_char, empty_char = random.choice(self.progress_bar_styles)
        bar = full_char * progress + empty_char * (bar_length - progress)
        return bar

    async def get_dominant_color_from_image(self, image_url):
        """Asynchronously extract the dominant color from an image URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        img = Image.open(BytesIO(image_data))
                        img = img.convert("RGB")
                        img = img.resize((1, 1))
                        dominant_color = img.getpixel((0, 0))
                        return discord.Color.from_rgb(*dominant_color)
                    else:
                        logger.error(f"Failed to fetch image: Status {response.status}")
                        return discord.Color.blurple()
        except Exception:
            logger.exception("Exception occurred while fetching dominant color:")
            return discord.Color.blurple()

    async def get_random_level_up_message(self, user):
        """Returns a random level-up message."""
        level_data = await self.db.get_user_level(str(user.guild.id), str(user.id))
        current_level = level_data["level"]
        
        messages = [
            f"🎉 {user.mention} leveled up! You're on fire!",
            f"🔥 {user.mention} just hit a new level! Keep it up!",
            f"🚀 {user.mention} has leveled up! You're unstoppable!",
            f"🎇 {user.mention}, you leveled up! Keep climbing!",
            f"✨ {user.mention} is now stronger at level {current_level}!",
            f"⚡ {user.mention}, you've reached new heights at level {current_level}!",
            f"🌠 Incredible! {user.mention} is now at level {current_level}!",
            f"🌟 Whoa! {user.mention} just advanced to level {current_level}! Amazing job!",
            f"🥳 Look at that! {user.mention} leveled up to {current_level}!",
            f"💫 Keep shining, {user.mention}! You've reached level {current_level}!",
            f"🎖️ Impressive, {user.mention}! Level {current_level} is yours!",
            f"📈 {user.mention} just leveled up to {current_level}! Keep the momentum going!",
            f"🏆 Bravo {user.mention}! You've climbed to level {current_level}!",
            f"🔥 Keep the heat up, {user.mention}! You've unlocked level {current_level}!",
            f"✨ {user.mention} just reached level {current_level}! Onwards and upwards!",
        ]
        return random.choice(messages)

    @commands.command(name="setlevelchannel")
    @commands.has_permissions(administrator=True)
    async def set_level_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel where level-up messages will be sent."""
        if channel is None:
            channel = ctx.channel

        await self.db.set_level_channel(str(ctx.guild.id), channel.id)
        await ctx.send(f"Level-up messages will be sent to {channel.mention}")


    @commands.command(name="restrictxpchannel")
    @commands.has_permissions(administrator=True)
    async def restrict_xp_channel(self, ctx, channel: discord.TextChannel = None):
        """Toggle restriction of a channel from awarding XP."""
        if channel is None:
            channel = ctx.channel

        is_restricted = await self.db.toggle_restricted_entity(
            str(ctx.guild.id), 
            str(channel.id), 
            'channel'
        )

        if is_restricted:
            await ctx.send(f"{channel.mention} is now restricted from awarding XP.")
        else:
            await ctx.send(f"{channel.mention} is no longer restricted from awarding XP.")


    @commands.command(name="restrictxpuser")
    @commands.has_permissions(administrator=True)
    async def restrict_xp_user(self, ctx, member: discord.Member):
        """Restrict or unrestrict a user from gaining XP in the server."""
        is_restricted = await self.db.toggle_restricted_entity(
            str(ctx.guild.id), 
            str(member.id), 
            'user'
        )

        if is_restricted:
            await ctx.send(f"{member.mention} is now restricted from gaining XP.")
        else:
            await ctx.send(f"{member.mention} is no longer restricted from gaining XP.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle incoming messages for XP awarding and command processing."""
        if message.author.bot or message.guild is None:
            return

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        channel_id = message.channel.id

        # Check for restrictions
        if await self.is_user_restricted(guild_id, user_id):
            return

        # Check if channel is restricted
        async with aiosqlite.connect(self.db.db_path) as db:
            async with db.execute(
                'SELECT 1 FROM restricted_entities WHERE guild_id = ? AND entity_id = ? AND entity_type = ?',
                (guild_id, str(channel_id), 'channel')
            ) as cursor:
                if await cursor.fetchone():
                    return

        # Award XP if the user can receive it
        if await self.can_receive_xp(guild_id, user_id):
            guild_config = await self.db.get_guild_config(guild_id)
            xp_amount = guild_config.get('xp_amount', 10)
            leveled_up = await self.add_xp(guild_id, user_id, xp_amount)

            if leveled_up:
                level_channel_id = guild_config.get('level_channel_id', message.channel.id)
                level_up_channel = message.guild.get_channel(level_channel_id) or message.channel

                level_up_message = await self.get_random_level_up_message(message.author)
                await level_up_channel.send(level_up_message)

                # Handle role assignment
                level_roles = await self.db.get_level_roles(guild_id)
                user_level = (await self.db.get_user_level(guild_id, user_id))['level']
                
                for level, role_id in level_roles:
                    if level == user_level:
                        role = message.guild.get_role(role_id)
                        if role:
                            try:
                                await message.author.add_roles(role)
                                await level_up_channel.send(f"{message.author.mention} has been awarded the role: {role.name}!")
                            except discord.Forbidden:
                                await level_up_channel.send(f"I don't have permission to assign the role {role.name}.")
                            except discord.HTTPException:
                                await level_up_channel.send(f"Failed to assign the role {role.name} due to a network error.")


    @commands.command(name="level")
    @commands.cooldown(1, 30, BucketType.user)
    async def check_level(self, ctx, member: discord.Member = None):
        """Check the level and XP of a user in the current guild, with a fancy embed."""
        if member is None:
            member = ctx.author
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        level_data = await self.db.get_user_level(str(ctx.guild.id), str(member.id))
        xp = level_data["xp"]
        level = level_data["level"]

        # XP needed for the next level
        xp_needed = self.xp_for_next_level(level)

        # XP remaining to level up
        xp_remaining = xp_needed - xp

        # Progress bar
        progress_bar = self.create_progress_bar(xp, xp_needed)

        # User's avatar URL
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url

        # Get the dominant color from the avatar image
        embed_color = await self.get_dominant_color_from_image(str(avatar_url))

        # Create the embed message
        embed = discord.Embed(
            title=f"{member.name}'s Level Information",
            description=f"**Level**: {level}\n**XP**: {xp}/{xp_needed} XP\n\n{progress_bar}",
            color=embed_color
        )

        # Add avatar as thumbnail
        embed.set_thumbnail(url=avatar_url)

        # Add more details about the XP remaining
        embed.add_field(name="XP Remaining", value=f"{xp_remaining} XP until next level", inline=False)

        # Send the embed
        await ctx.send(embed=embed)

    @commands.command(name="createevent")
    @commands.has_permissions(administrator=True)
    async def create_xp_event(self, ctx, name: str, multiplier: float, duration: int, *roles: discord.Role):
        """Create a temporary XP boost event."""
        if multiplier <= 0:
            await ctx.send("Multiplier must be greater than 0.")
            return

        if duration <= 0:
            await ctx.send("Duration must be greater than 0 hours.")
            return

        role_ids = [role.id for role in roles] if roles else None
        end_time = await self.db.create_xp_event(str(ctx.guild.id), name, multiplier, duration, role_ids)

        embed = discord.Embed(
            title="🎉 XP Boost Event Created!",
            description=f"**{name}** is now active!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Multiplier", value=f"{multiplier}x XP", inline=True)
        embed.add_field(name="Duration", value=f"{duration} hours", inline=True)
        embed.add_field(name="Ends At", value=end_time.strftime("%Y-%m-%d %H:%M UTC"), inline=True)
        
        if roles:
            embed.add_field(
                name="Affected Roles", 
                value="\n".join(role.mention for role in roles),
                inline=False
            )
        else:
            embed.add_field(name="Affects", value="All members", inline=False)

        await ctx.send(embed=embed)


    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 5, BucketType.user) 
    async def grantxp(self, ctx, user: discord.User, amount: int):
        """Grant a specified amount of XP to a user."""
        guild_id = str(ctx.guild.id)
        user_id = str(user.id)

        # Grant XP and check if leveled up
        leveled_up, new_level, _ = await self.db.add_xp(guild_id, user_id, amount)

        if leveled_up:
            # Get role for the new level if it exists
            level_roles = await self.db.get_level_roles(guild_id)
            for level, role_id in level_roles:
                if level == new_level:
                    role = ctx.guild.get_role(role_id)
                    if role:
                        try:
                            await ctx.guild.get_member(int(user_id)).add_roles(role)
                            await ctx.send(f"{user.mention} has been granted {amount} XP, leveled up, and received the {role.name} role!")
                            return
                        except (discord.Forbidden, discord.HTTPException):
                            await ctx.send(f"{user.mention} has been granted {amount} XP and leveled up, but I couldn't assign the role.")
                            return
            
            await ctx.send(f"{user.mention} has been granted {amount} XP and leveled up!")
        else:
            await ctx.send(f"{user.mention} has been granted {amount} XP!")

    @commands.command(name="bulkgrantxp")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 30, BucketType.guild)
    async def bulk_grant_xp(self, ctx, amount: int, *members: discord.Member):
        """Grant XP to multiple users at once."""
        if not members:
            await ctx.send("Please specify at least one member to grant XP to.")
            return

        if len(members) > 25:
            await ctx.send("You can only grant XP to up to 25 members at once.")
            return

        user_xp_mapping = {str(member.id): amount for member in members}
        results = await self.db.bulk_add_xp(str(ctx.guild.id), user_xp_mapping)

        # Process results and handle role assignments
        level_roles = await self.db.get_level_roles(str(ctx.guild.id))
        
        success_msg = f"Granted {amount} XP to {len(members)} members.\n"
        level_ups = []

        for user_id, leveled_up, new_level in results:
            member = ctx.guild.get_member(int(user_id))
            if leveled_up:
                level_ups.append(f"{member.mention} reached level {new_level}!")
                
                # Handle role assignment
                for level, role_id in level_roles:
                    if level == new_level:
                        role = ctx.guild.get_role(role_id)
                        if role:
                            try:
                                await member.add_roles(role)
                                level_ups.append(f"{member.mention} received the {role.name} role!")
                            except discord.Forbidden:
                                level_ups.append(f"Couldn't assign {role.name} role to {member.mention}.")

        if level_ups:
            success_msg += "\n" + "\n".join(level_ups)

        await ctx.send(success_msg)

    @commands.command(name="setmultiplier")
    @commands.has_permissions(administrator=True)
    async def set_multiplier(self, ctx, multiplier: float, duration: int = None, target: Union[discord.Role, discord.Member] = None):
        """Set XP multiplier for the server, role, or user."""
        if multiplier <= 0:
            await ctx.send("Multiplier must be greater than 0.")
            return

        guild_id = str(ctx.guild.id)
        if target is None:
            # Server-wide multiplier
            await self.db.set_xp_multiplier(guild_id, "server", guild_id, multiplier, duration)
            duration_text = f" for {duration} hours" if duration else " permanently"
            await ctx.send(f"Server-wide XP multiplier set to {multiplier}x{duration_text}.")
        else:
            # Role or user multiplier
            multiplier_type = "role" if isinstance(target, discord.Role) else "user"
            await self.db.set_xp_multiplier(guild_id, multiplier_type, str(target.id), multiplier, duration)
            await ctx.send(f"XP multiplier for {target.name} set to {multiplier}x{' for ' + str(duration) + ' hours' if duration else ''}.")

    @commands.command(name="multipliers")
    async def view_multipliers(self, ctx):
        """View all active XP multipliers in the server."""
        multipliers = await self.db.get_active_multipliers(str(ctx.guild.id))
        
        if not multipliers:
            await ctx.send("No active XP multipliers.")
            return

        embed = discord.Embed(title="Active XP Multipliers", color=discord.Color.blue())
        
        for m_type, target_id, multiplier, expires_at in multipliers:
            if m_type == "server":
                name = "Server-wide"
            elif m_type == "role":
                role = ctx.guild.get_role(int(target_id))
                name = f"Role: {role.name}" if role else "Unknown Role"
            else:
                user = ctx.guild.get_member(int(target_id))
                name = f"User: {user.name}" if user else "Unknown User"
                
            value = f"{multiplier}x"
            if expires_at:
                time_left = expires_at - datetime.now()
                hours_left = int(time_left.total_seconds() / 3600)
                value += f"\nExpires in {hours_left} hours"
                
            embed.add_field(name=name, value=value, inline=False)
        
        await ctx.send(embed=embed)


    @commands.command(name="resetxp")
    @commands.has_permissions(manage_roles=True)
    async def reset_xp(self, ctx, member: discord.Member = None):
        """Reset a user's XP and level in the current guild."""
        if member is None:
            member = ctx.author

        guild_id = str(ctx.guild.id)
        
        # Get all level roles for this guild
        level_roles = await self.db.get_level_roles(guild_id)
        
        # Remove level-specific roles from the user
        roles_removed = []
        for _, role_id in level_roles:
            role = ctx.guild.get_role(role_id)
            if role and role in member.roles:
                try:
                    await member.remove_roles(role)
                    roles_removed.append(role.name)
                except discord.Forbidden:
                    await ctx.send(f"I don't have permission to remove the role {role.name}.")
                except discord.HTTPException:
                    await ctx.send(f"Failed to remove the role {role.name} due to a network error.")

        # Reset the user's XP and level in database
        await self.db.reset_user_level(guild_id, str(member.id))

        # Send confirmation message
        if roles_removed:
            await ctx.send(f"{member.mention}'s XP and level have been reset. Removed roles: {', '.join(roles_removed)}")
        else:
            await ctx.send(f"{member.mention}'s XP and level have been reset.")


    @commands.command(name="toplevel")
    async def toplevel(self, ctx):
        """Display the top users by XP in the current guild, with avatars, sorted by level."""
        top_users = await self.db.get_top_users(str(ctx.guild.id))

        if top_users:
            user_count = len(top_users)
            width, height = 900, 100 + user_count * 80
            leaderboard_image = Image.new("RGB", (width, height), color=(30, 30, 30))

            draw = ImageDraw.Draw(leaderboard_image)
            font_path = "assets/fonts/segoe-ui-semibold.ttf"
            font = ImageFont.truetype(font_path, 30)

            y_offset = 40

            for i, (user_id, level, xp) in enumerate(top_users, 1):
                user = self.bot.get_user(int(user_id))
                if user:
                    avatar_asset = user.avatar or user.default_avatar
                    avatar_bytes = await avatar_asset.read()
                    avatar_image = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
                    avatar_image = avatar_image.resize((50, 50))

                    mask = avatar_image.split()[3]
                    leaderboard_image.paste(avatar_image, (50, y_offset), mask)

                    draw.text(
                        (120, y_offset + 10),
                        f"{i}. {user.name} - Level {level} ({xp} XP)",
                        fill=(255, 255, 255),
                        font=font
                    )

                    y_offset += 80

            with BytesIO() as image_binary:
                leaderboard_image.save(image_binary, 'PNG')
                image_binary.seek(0)

                file = discord.File(fp=image_binary, filename="leaderboard.png")
                embed = discord.Embed(
                    title=f"{ctx.guild.name} Leaderboard",
                    description="Here's the top 10 users of this server.",
                    color=discord.Color.blurple()
                )
                embed.set_image(url="attachment://leaderboard.png")

                await ctx.send(file=file, embed=embed)
        else:
            await ctx.send("No users have XP in this server yet.")


    @commands.command(name="resetxp")
    @commands.has_permissions(manage_roles=True)
    async def reset_xp(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        await self.db.reset_user_level(str(ctx.guild.id), str(member.id))
        await ctx.send(f"{member.mention}'s XP and level have been reset.")

    @commands.command(name="setlevelrole")
    @commands.has_permissions(manage_roles=True)
    async def set_level_role(self, ctx, level: int, role: discord.Role):
        await self.db.set_level_role(str(ctx.guild.id), level, role.id)
        
        embed = discord.Embed(
            title="Level-Up Role Set",
            description=f"The role **{role.name}** will now be assigned when users reach level **{level}**.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Level", value=f"{level}", inline=True)
        embed.add_field(name="Role", value=f"{role.name}", inline=True)
        embed.set_footer(text=f"Configured by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="viewlevelroles")
    @commands.has_permissions(manage_roles=True)
    async def view_level_roles(self, ctx):
        roles = await self.db.get_level_roles(str(ctx.guild.id))
        
        if roles:
            embed = discord.Embed(
                title=f"Level-Up Roles for {ctx.guild.name}",
                description="Here are the roles assigned for specific levels:",
                color=discord.Color.green()
            )
            
            for level, role_id in roles:
                role = ctx.guild.get_role(role_id)
                if role:
                    embed.add_field(name=f"Level {level}", value=f"{role.name}", inline=False)
        else:
            embed = discord.Embed(
                title="No Level-Up Roles Configured",
                description="There are no roles set for any levels in this server.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed)


    @commands.command(name="setlevelrole")
    @commands.has_permissions(manage_roles=True)
    async def set_level_role(self, ctx, level: int, role: discord.Role):
        await self.db.set_level_role(str(ctx.guild.id), level, role.id)
        
        embed = discord.Embed(
            title="Level-Up Role Set",
            description=f"The role **{role.name}** will now be assigned when users reach level **{level}**.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Level", value=f"{level}", inline=True)
        embed.add_field(name="Role", value=f"{role.name}", inline=True)
        embed.set_footer(text=f"Configured by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)
        
    @commands.command(name="setxpcooldown")
    @commands.has_permissions(administrator=True)
    async def set_xp_cooldown(self, ctx, seconds: int):
        """Set the cooldown time (in seconds) between XP gains."""
        await self.db.update_xp_settings(str(ctx.guild.id), cooldown=seconds)
        await ctx.send(f"XP cooldown has been set to {seconds} seconds.")


    @commands.command(name="setxpamount")
    @commands.has_permissions(administrator=True)
    async def set_xp_amount(self, ctx, amount: int):
        """Set the amount of XP awarded per message."""
        await self.db.update_xp_settings(str(ctx.guild.id), amount=amount)
        await ctx.send(f"XP amount per message has been set to {amount} XP.")


    @commands.command(name="togglexpblock")
    @commands.has_permissions(administrator=True)
    async def toggle_xp_block(self, ctx):
        """Toggle XP award blocking for the guild."""
        is_blocked = await self.db.toggle_guild_block(str(ctx.guild.id))
        
        if is_blocked:
            await ctx.send("XP award has been **blocked** for this guild.")
        else:
            await ctx.send("XP award has been **unblocked** for this guild.")

        await self.save_blocked_guilds()

async def setup(bot):
    await bot.add_cog(LevelSystem(bot))