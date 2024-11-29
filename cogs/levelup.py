import discord
from discord.ext import commands, tasks
from PIL import Image, ImageDraw, ImageFont
import aiofiles
import aiohttp
from io import BytesIO
import random
import os
import json
from datetime import datetime, timedelta, timezone
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.levels_file = 'cogs/data/levels.json'
        self.roles_file = 'cogs/data/roles.json'
        self.config_file = 'cogs/data/level_config.json'
        self.block_guild_file = 'cogs/data/blocked_guilds.json'
        self.last_message_time = {}
        self.blocked_guilds = set()
        self.levels = {}
        self.level_roles = {}
        self.config = {}

        # Start the background task for periodic saving
        self.save_task = self.bot.loop.create_task(self.periodic_save())

    async def cog_load(self):
        """Initialize the cog by loading data asynchronously."""
        await self.load_levels()
        await self.load_roles()
        await self.load_blocked_guilds()
        await self.load_config()

    def cog_unload(self):
        """Cleanup when the cog is unloaded."""
        self.save_task.cancel()
        self.bot.loop.create_task(self.save_all())

    async def periodic_save(self):
        """Periodically save data to disk."""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(300)  # Save every 5 minutes
            await self.save_all()

    async def save_all(self):
        """Save all data to disk."""
        await self.save_levels()
        await self.save_config()
        await self.save_roles()
        await self.save_blocked_guilds()

    async def load_roles(self):
        """Asynchronously load roles for level-ups from a JSON file."""
        try:
            if os.path.exists(self.roles_file):
                async with aiofiles.open(self.roles_file, 'r') as f:
                    data = await f.read()
                    self.level_roles = json.loads(data)
                    if not isinstance(self.level_roles, dict):
                        self.level_roles = {}
            else:
                self.level_roles = {}
        except Exception as e:
            logger.exception("Exception occurred while loading roles:")
            self.level_roles = {}

    async def save_roles(self):
        """Asynchronously save roles to a JSON file."""
        try:
            async with aiofiles.open(self.roles_file, 'w') as f:
                data = json.dumps(self.level_roles, indent=4)
                await f.write(data)
        except Exception as e:
            logger.exception("Exception occurred while saving roles:")

    async def load_levels(self):
        """Asynchronously load levels from a JSON file."""
        try:
            if os.path.exists(self.levels_file):
                async with aiofiles.open(self.levels_file, 'r') as f:
                    data = await f.read()
                    self.levels = json.loads(data)  # Corrected line
                    if not isinstance(self.levels, dict):
                        self.levels = {}
            else:
                self.levels = {}
        except Exception as e:
            logger.exception("Exception occurred while loading levels:")
            self.levels = {}

    async def save_levels(self):
        """Asynchronously save levels to a JSON file."""
        try:
            async with aiofiles.open(self.levels_file, 'w') as f:
                data = json.dumps(self.levels, indent=4)
                await f.write(data)
        except Exception as e:
            logger.exception("Exception occurred while saving levels:")

    async def load_config(self):
        """Asynchronously load the configuration for level-up and XP settings."""
        try:
            if os.path.exists(self.config_file):
                async with aiofiles.open(self.config_file, 'r') as f:
                    data = await f.read()
                    self.config = json.loads(data)
                    if not isinstance(self.config, dict):
                        self.config = {}
            else:
                self.config = {}
        except Exception as e:
            logger.exception("Exception occurred while loading config:")
            self.config = {}

    async def save_config(self):
        """Asynchronously save the configuration to a JSON file."""
        try:
            async with aiofiles.open(self.config_file, 'w') as f:
                data = json.dumps(self.config, indent=4)
                await f.write(data)
        except Exception as e:
            logger.exception("Exception occurred while saving config:")

    async def load_blocked_guilds(self):
        """Asynchronously load the list of blocked guilds from a JSON file."""
        try:
            if os.path.exists(self.block_guild_file):
                async with aiofiles.open(self.block_guild_file, 'r') as f:
                    data = await f.read()
                    self.blocked_guilds = set(json.loads(data))
            else:
                self.blocked_guilds = set()
        except Exception as e:
            logger.exception("Exception occurred while loading blocked guilds:")
            self.blocked_guilds = set()

    async def save_blocked_guilds(self):
        """Asynchronously save the list of blocked guilds to a JSON file."""
        try:
            async with aiofiles.open(self.block_guild_file, 'w') as f:
                data = json.dumps(list(self.blocked_guilds), indent=4)
                await f.write(data)
        except Exception as e:
            logger.exception("Exception occurred while saving blocked guilds:")

    def is_user_restricted(self, guild_id, user_id):
        """Check if a user is restricted from gaining XP."""
        return user_id in self.config.get(guild_id, {}).get('restricted_users', [])

    async def add_xp(self, guild_id, user_id, xp):
        """Add XP to a user and handle level-ups."""
        guild_id = str(guild_id)
        user_id = str(user_id)

        # Check if the guild is blocked from awarding XP
        if guild_id in self.blocked_guilds:
            return False  # Return early if XP award is blocked

        # Initialize levels if not already present
        if guild_id not in self.levels:
            self.levels[guild_id] = {}

        if user_id not in self.levels[guild_id]:
            self.levels[guild_id][user_id] = {"xp": 0, "level": 1}

        # Retrieve current level and XP
        current_level = self.levels[guild_id][user_id]["level"]
        current_xp = self.levels[guild_id][user_id]["xp"]

        # Add the granted XP to current XP
        current_xp += xp

        # Level-up logic
        leveled_up = False
        while True:
            # Calculate the XP required for the next level
            xp_needed = self.xp_for_next_level(current_level)

            # Check if the current XP is enough to level up
            if current_xp >= xp_needed:
                current_xp -= xp_needed
                current_level += 1
                leveled_up = True
            else:
                break

        # Update the user's level and remaining XP
        self.levels[guild_id][user_id]["xp"] = current_xp
        self.levels[guild_id][user_id]["level"] = current_level

        # Return True if a level-up occurred
        return leveled_up

    def xp_for_next_level(self, level):
        """Calculate the XP required for the next level."""
        return int(100 * (level ** 1.5))

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
        except Exception as e:
            logger.exception("Exception occurred while fetching dominant color:")
            return discord.Color.blurple()

    def create_progress_bar(self, current_xp, xp_needed, bar_length=20):
        """Generate a progress bar for the level embed."""
        progress = int((current_xp / xp_needed) * bar_length)
        bar = "█" * progress + "░" * (bar_length - progress)
        return bar

    def get_random_level_up_message(self, user):
        """Returns a random level-up message."""
        messages = [
            f"🎉 {user.mention} leveled up! You're on fire!",
            f"🔥 {user.mention} just hit a new level! Keep it up!",
            f"🚀 {user.mention} has leveled up! You're unstoppable!",
            f"🎇 {user.mention}, you leveled up! Keep climbing!",
            f"✨ {user.mention} is now stronger at level {self.levels[str(user.guild.id)][str(user.id)]['level']}!",
            f"⚡ {user.mention}, you've reached new heights at level {self.levels[str(user.guild.id)][str(user.id)]['level']}!",
            f"🌠 Incredible! {user.mention} is now at level {self.levels[str(user.guild.id)][str(user.id)]['level']}!",
            f"🌟 Whoa! {user.mention} just advanced to level {self.levels[str(user.guild.id)][str(user.id)]['level']}! Amazing job!",
            f"🥳 Look at that! {user.mention} leveled up to {self.levels[str(user.guild.id)][str(user.id)]['level']}!",
            f"💫 Keep shining, {user.mention}! You've reached level {self.levels[str(user.guild.id)][str(user.id)]['level']}!",
            f"🎖️ Impressive, {user.mention}! Level {self.levels[str(user.guild.id)][str(user.id)]['level']} is yours!",
            f"📈 {user.mention} just leveled up to {self.levels[str(user.guild.id)][str(user.id)]['level']}! Keep the momentum going!",
            f"🏆 Bravo {user.mention}! You've climbed to level {self.levels[str(user.guild.id)][str(user.id)]['level']}!",
            f"🔥 Keep the heat up, {user.mention}! You've unlocked level {self.levels[str(user.guild.id)][str(user.id)]['level']}!",
            f"✨ {user.mention} just reached level {self.levels[str(user.guild.id)][str(user.id)]['level']}! Onwards and upwards!",
        ]
        return random.choice(messages)

    def can_receive_xp(self, guild_id, user_id):
        """Check if enough time has passed to receive more XP."""
        now = datetime.now(timezone.utc)
        cooldown = self.config.get(guild_id, {}).get('xp_cooldown', 10)  # Default 10 seconds
        last_time = self.last_message_time.get((guild_id, user_id))

        if last_time is None or (now - last_time).total_seconds() >= cooldown:
            self.last_message_time[(guild_id, user_id)] = now
            return True
        return False

    @commands.command(name="setlevelchannel")
    @commands.has_permissions(administrator=True)
    async def set_level_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel where level-up messages will be sent."""
        guild_id = str(ctx.guild.id)
        if channel is None:
            channel = ctx.channel  # Default to current channel if none is specified

        if guild_id not in self.config:
            self.config[guild_id] = {}

        self.config[guild_id]['level_channel'] = channel.id
        await self.save_config()

        await ctx.send(f"Level-up messages will be sent to {channel.mention}")

    @commands.command(name="restrictxpchannel")
    @commands.has_permissions(administrator=True)
    async def restrict_xp_channel(self, ctx, channel: discord.TextChannel = None):
        """Toggle restriction of a channel from awarding XP."""
        guild_id = str(ctx.guild.id)
        if channel is None:
            channel = ctx.channel  # Default to current channel if none is specified

        if guild_id not in self.config:
            self.config[guild_id] = {}

        if 'restricted_channels' not in self.config[guild_id]:
            self.config[guild_id]['restricted_channels'] = []

        # Toggle the restriction
        if channel.id in self.config[guild_id]['restricted_channels']:
            self.config[guild_id]['restricted_channels'].remove(channel.id)
            await ctx.send(f"{channel.mention} is no longer restricted from awarding XP.")
        else:
            self.config[guild_id]['restricted_channels'].append(channel.id)
            await ctx.send(f"{channel.mention} is now restricted from awarding XP.")

        await self.save_config()

    @commands.command(name="restrictxpuser")
    @commands.has_permissions(administrator=True)
    async def restrict_xp_user(self, ctx, member: discord.Member):
        """Restrict or unrestrict a user from gaining XP in the server."""
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id not in self.config:
            self.config[guild_id] = {}

        if 'restricted_users' not in self.config[guild_id]:
            self.config[guild_id]['restricted_users'] = []

        if user_id in self.config[guild_id]['restricted_users']:
            self.config[guild_id]['restricted_users'].remove(user_id)
            await ctx.send(f"{member.mention} is no longer restricted from gaining XP.")
        else:
            self.config[guild_id]['restricted_users'].append(user_id)
            await ctx.send(f"{member.mention} is now restricted from gaining XP.")

        await self.save_config()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle incoming messages for XP awarding and command processing."""
        if message.author.bot or message.guild is None:
            return

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        channel_id = message.channel.id

        # Check for restrictions
        if self.is_user_restricted(guild_id, user_id) or \
           (guild_id in self.config and 'restricted_channels' in self.config[guild_id] and channel_id in self.config[guild_id]['restricted_channels']):
            return

        # Award XP if the user can receive it
        if self.can_receive_xp(guild_id, user_id):
            xp_amount = self.config.get(guild_id, {}).get('xp_amount', 10)  # Default 10 XP
            leveled_up = await self.add_xp(guild_id, user_id, xp_amount)

            if leveled_up:
                level_up_channel_id = self.config.get(guild_id, {}).get('level_channel', message.channel.id)
                level_up_channel = message.guild.get_channel(level_up_channel_id) or message.channel

                level_up_message = self.get_random_level_up_message(message.author)
                await level_up_channel.send(level_up_message)

                # Assign role if available for the new level
                new_level = self.levels[guild_id][user_id]["level"]
                if guild_id in self.level_roles and str(new_level) in self.level_roles[guild_id]:
                    role_id = self.level_roles[guild_id][str(new_level)]
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
    async def check_level(self, ctx, member: discord.Member = None):
        """Check the level and XP of a user in the current guild, with a fancy embed."""
        if member is None:
            member = ctx.author
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id in self.levels and user_id in self.levels[guild_id]:
            xp = self.levels[guild_id][user_id]["xp"]
            level = self.levels[guild_id][user_id]["level"]

            # Correct XP needed for the next level
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
        else:
            await ctx.send(f"{member.mention} has no XP yet in this server.")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def grantxp(self, ctx, user: discord.User, amount: int):
        """Grant a specified amount of XP to a user."""
        guild_id = str(ctx.guild.id)
        user_id = str(user.id)

        if guild_id not in self.levels:
            self.levels[guild_id] = {}

        if user_id not in self.levels[guild_id]:
            self.levels[guild_id][user_id] = {"xp": 0, "level": 1}

        # Grant XP
        leveled_up = await self.add_xp(guild_id, user_id, amount)

        if leveled_up:
            await ctx.send(f"{user.mention} has been granted {amount} XP and leveled up!")
        else:
            await ctx.send(f"{user.mention} has been granted {amount} XP!")

    @commands.command(name="resetxp")
    @commands.has_permissions(manage_roles=True)
    async def reset_xp(self, ctx, member: discord.Member = None):
        """Reset a user's XP and level in the current guild."""
        if member is None:
            member = ctx.author

        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        # Check if the user has any XP/level data in the current guild
        if guild_id in self.levels and user_id in self.levels[guild_id]:
            # Reset XP and level for the user
            self.levels[guild_id][user_id] = {"xp": 0, "level": 1}

            # Remove level-specific roles, if any, associated with this guild
            if guild_id in self.level_roles:
                user_roles = self.level_roles[guild_id]
                for level, role_id in user_roles.items():
                    role = ctx.guild.get_role(role_id)
                    if role in member.roles:
                        try:
                            await member.remove_roles(role)
                        except discord.Forbidden:
                            await ctx.send(f"I don't have permission to remove the role {role.name}.")
                        except discord.HTTPException:
                            await ctx.send(f"Failed to remove the role {role.name} due to a network error.")

            await self.save_levels()
            await ctx.send(f"{member.mention}'s XP and level have been reset.")
        else:
            await ctx.send(f"{member.mention} has no XP or level data to reset.")

    @commands.command(name="toplevel")
    async def toplevel(self, ctx):
        """Display the top users by XP in the current guild, with avatars, sorted by level."""
        guild_id = str(ctx.guild.id)

        if guild_id in self.levels:
            sorted_users = sorted(
                self.levels[guild_id].items(),
                key=lambda x: x[1]["level"],
                reverse=True
            )

            if sorted_users:
                top_users = sorted_users[:10]
                user_count = len(top_users)
                width, height = 900, 100 + user_count * 80
                leaderboard_image = Image.new("RGB", (width, height), color=(30, 30, 30))

                draw = ImageDraw.Draw(leaderboard_image)
                font_path = "assets/fonts/segoe-ui-semibold.ttf"  # Ensure this path is correct
                font = ImageFont.truetype(font_path, 30)

                y_offset = 40

                for i, (user_id, data) in enumerate(top_users, 1):
                    user = self.bot.get_user(int(user_id))
                    if user:
                        level = data["level"]
                        xp = data["xp"]

                        # Use Discord's Asset.read to fetch avatar bytes
                        avatar_asset = user.avatar or user.default_avatar
                        avatar_bytes = await avatar_asset.read()
                        avatar_image = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
                        avatar_image = avatar_image.resize((50, 50))

                        # Paste avatar onto leaderboard
                        mask = avatar_image.split()[3]  # Use alpha channel as mask
                        leaderboard_image.paste(avatar_image, (50, y_offset), mask)

                        # Add text
                        draw.text(
                            (120, y_offset + 10),
                            f"{i}. {user.name} - Level {level} ({xp} XP)",
                            fill=(255, 255, 255),
                            font=font
                        )

                        y_offset += 80

                # Save the image to a BytesIO object and send it
                with BytesIO() as image_binary:
                    leaderboard_image.save(image_binary, 'PNG')
                    image_binary.seek(0)

                    file = discord.File(fp=image_binary, filename="leaderboard.png")
                    embed = discord.Embed(
                        title=f"{ctx.guild.name} Leaderboard",
                        description="Here's the top 10 users of this server.",
                        color=discord.Color.blurple()
                    )
                    embed.set_image(url="attachment://leaderboard.png")  # Attach the image

                    await ctx.send(file=file, embed=embed)

            else:
                await ctx.send("No users have leveled up yet.")
        else:
            await ctx.send("No users have XP in this server yet.")

    @commands.command(name="viewlevelroles")
    @commands.has_permissions(manage_roles=True)
    async def view_level_roles(self, ctx):
        """View all the level-up roles set in the current guild."""
        guild_id = str(ctx.guild.id)

        if guild_id in self.level_roles and self.level_roles[guild_id]:
            embed = discord.Embed(
                title=f"Level-Up Roles for {ctx.guild.name}",
                description="Here are the roles assigned for specific levels:",
                color=discord.Color.green()
            )

            for lvl, role_id in self.level_roles[guild_id].items():
                role = ctx.guild.get_role(role_id)
                if role:
                    embed.add_field(name=f"Level {lvl}", value=f"{role.name}", inline=False)

            await ctx.send(embed=embed)
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
        """Set a role to be given when a user reaches a specific level."""
        guild_id = str(ctx.guild.id)

        if guild_id not in self.level_roles:
            self.level_roles[guild_id] = {}

        self.level_roles[guild_id][str(level)] = role.id
        await self.save_roles()

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
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}

        self.config[guild_id]['xp_cooldown'] = seconds
        await self.save_config()
        await ctx.send(f"XP cooldown has been set to {seconds} seconds.")

    @commands.command(name="setxpamount")
    @commands.has_permissions(administrator=True)
    async def set_xp_amount(self, ctx, amount: int):
        """Set the amount of XP awarded per message."""
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}

        self.config[guild_id]['xp_amount'] = amount
        await self.save_config()
        await ctx.send(f"XP amount per message has been set to {amount} XP.")

    @commands.command(name="togglexpblock")
    @commands.has_permissions(administrator=True)
    async def toggle_xp_block(self, ctx):
        """Toggle XP award blocking for the guild."""
        guild_id = str(ctx.guild.id)

        if guild_id in self.blocked_guilds:
            self.blocked_guilds.remove(guild_id)
            await ctx.send(f"XP award has been **unblocked** for this guild.")
        else:
            self.blocked_guilds.add(guild_id)
            await ctx.send(f"XP award has been **blocked** for this guild.")

        await self.save_blocked_guilds()

async def setup(bot):
    await bot.add_cog(LevelSystem(bot))