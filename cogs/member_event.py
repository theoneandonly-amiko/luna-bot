import discord
from discord.ext import commands
from discord.utils import utcnow
import asyncio
from datetime import timedelta
import json
import os
from pathlib import Path
import random
import re

class WelcomeGoodbyeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings_file = "cogs/data/guild_settings.json"
        self.guild_settings = self.load_guild_settings()
        self.lock = asyncio.Lock()

        # Randomized welcome and goodbye messages
        self.default_greet_messages = [
            "Welcome to the server, {mention}! 🎉",
            "Hey {mention}, glad you joined us! 😊",
            "{mention}, we hope you have a great time here! ✨",
            "Hooray! {mention} is here! 🙌",
            "Look who just joined! Welcome, {mention}! 🎊",
            "We're thrilled to have you, {mention}! 🥳",
            "A warm welcome to {mention}! 🌟 Make yourself at home.",
            "It's awesome to see you here, {mention}! 🌈",
            "{mention}, welcome aboard! We're going to have a blast! 🎉",
            "{mention} has arrived! Let's get the party started! 🎶",
            "Hey {mention}! We're so happy you're here! 💫",
            "{mention}, you're finally here! Everyone, say hi! 👋",
            "Big cheers for {mention}! 🎈 Let's make some memories together.",
            "{mention}, welcome to the coolest place on Discord! 😎",
            "Nice to meet you, {mention}! We’ve been waiting for you! 🌄",
            "Welcome, {mention}! Ready to dive in and have fun? 🌊",
            "{mention}, you made it! Welcome to our awesome community! 🎇",
            "Happy to see you here, {mention}! Let's have a great time! 😊",
            "A big hello to {mention}! Make yourself comfortable! 🎈"
        ]

        
        self.default_goodbye_messages = [
            "Goodbye {name}, we will miss you! 😢",
            "{name} just left the server. Take care! 💔",
            "It was great having you with us, {name}. See you soon! 🌟",
            "{name}, we hope to see you again! 👋",
            "Sad to see you go, {name}. Until next time! 😥",
            "Farewell, {name}. The server won’t be the same without you! 😔",
            "{name} left the chat. Safe travels and come back soon! 🌍",
            "We’ll miss you, {name}. Best of luck on your journey! 🚀",
            "Take care, {name}. You’re always welcome back! 🌠",
            "{name}, our time together was amazing. Don’t be a stranger! 💌",
            "Until next time, {name}! Hope to see you again someday! 🌅",
            "{name}, may your next adventure be even more exciting! 🎒",
            "It was wonderful having you here, {name}. See you around! 🌻",
            "{name} has signed off. We’ll keep the memories close! 💭",
            "{name}, the server won’t feel the same without you. 👋",
            "Safe travels, {name}. Don’t forget us! 🌠",
            "We’ll keep your seat warm, {name}! Take care! 🪑",
            "{name}, you’ll always be part of our community! 💙",
            "Wishing you all the best, {name}. Come back anytime! 🌈",
        ]


        # Load guild settings from a JSON file
    def load_guild_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading guild settings: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        return {}

    # Save guild settings to a JSON file
    def save_guild_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.guild_settings, f, indent=4)
        except Exception as e:
            print(f"Error saving guild settings: {e}")

    def get_random_image(self, directory):
        directory = Path(directory)
        if not directory.exists():
            print(f"Directory {directory} does not exist.")
            return None
        # Get all .gif, .png, and .webp files in the specified directory
        image_files = list(directory.glob('*.gif')) + list(directory.glob('*.png')) + list(directory.glob('*.webp'))
        
        # If there are no image files, return None
        if not image_files:
            return None

        # Choose a random image file
        return random.choice(image_files)


    @commands.command(name="setgreetchannel")
    @commands.has_permissions(administrator=True)
    async def set_greet_channel(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            await ctx.send("Please mention a valid channel or provide a channel ID. Example: `&setgreetchannel #welcome`.")
            return

        async with self.lock:
            guild_id = str(ctx.guild.id)
            if guild_id not in self.guild_settings:
                self.guild_settings[guild_id] = {}
            self.guild_settings[guild_id]["greet_channel"] = channel.id
            self.save_guild_settings()  # Save after setting

        await ctx.send(f"Greeting channel set to {channel.mention}")

    @commands.command(name="setgoodbyechannel")
    @commands.has_permissions(administrator=True)
    async def set_goodbye_channel(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            await ctx.send("Please mention a valid channel or provide a channel ID. Example: `&setgoodbyechannel #goodbye`.")
            return
        async with self.lock:
            guild_id = str(ctx.guild.id)
            if guild_id not in self.guild_settings:
                self.guild_settings[guild_id] = {}
            self.guild_settings[guild_id]["goodbye_channel"] = channel.id
            self.save_guild_settings()  # Save after setting
            await ctx.send(f"Goodbye channel set to {channel.mention}")


    @commands.command(name="configuremessages")
    @commands.has_permissions(manage_guild=True)
    async def configure_messages(self, ctx):
        """Guides the moderator through configuring welcome, goodbye, and new account messages."""
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        guild_id = str(ctx.guild.id)
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {}

        await ctx.send(
            "Let's configure your custom messages! You can type `cancel` at any time to stop the setup.\n"
            "Available placeholders you can use in your messages:\n"
            "- `{mention}`: Member mention (e.g., @username)\n"
            "- `{name}`: Member's username\n"
            "- `{server}`: Server name\n"
            "- `{member_count}`: Server's member count\n"
            "- `{age}`: Account age (only in new account message)\n"
        )

        # Step 1: Welcome Message
        await ctx.send(
            "**Step 1:** Please provide your **welcome message** in the format `Title | Description`.\n"
            "You can use placeholders like `{mention}`, `{name}`, `{server}`, `{member_count}` in your message."
        )
        try:
            msg = await self.bot.wait_for('message', timeout=120.0, check=check)
            if msg.content.lower() == 'cancel':
                await ctx.send("Configuration canceled.")
                return
            welcome_input = msg.content.split('|', 1)
            if len(welcome_input) != 2:
                await ctx.send("Invalid format. Please use `Title | Description`.")
                return
            welcome_title = welcome_input[0].strip()
            welcome_description = welcome_input[1].strip()
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Configuration canceled.")
            return

        # Step 2: Goodbye Message
        await ctx.send(
            "**Step 2:** Please provide your **goodbye message** in the format `Title | Description`.\n"
            "You can use placeholders like `{name}`, `{server}`, `{member_count}` in your message."
        )
        try:
            msg = await self.bot.wait_for('message', timeout=120.0, check=check)
            if msg.content.lower() == 'cancel':
                await ctx.send("Configuration canceled.")
                return
            goodbye_input = msg.content.split('|', 1)
            if len(goodbye_input) != 2:
                await ctx.send("Invalid format. Please use `Title | Description`.")
                return
            goodbye_title = goodbye_input[0].strip()
            goodbye_description = goodbye_input[1].strip()
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Configuration canceled.")
            return

        # Step 3: New Account Message
        await ctx.send(
            "**Step 3:** Please provide your **new account message** description.\n"
            "You can use placeholders like `{mention}`, `{name}`, `{age}`, `{server}` in your message."
        )
        try:
            msg = await self.bot.wait_for('message', timeout=120.0, check=check)
            if msg.content.lower() == 'cancel':
                await ctx.send("Configuration canceled.")
                return
            new_account_description = msg.content.strip()
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Configuration canceled.")
            return

        # Step 4: Custom Images
        # Welcome Image
        await ctx.send("**Step 4:** Do you want to use the **default welcome image**? Please note that you should not delete the uploaded photos for this item, otherwise the feature will use the available image set by default. Type `yes` or `no`:")
        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
            if msg.content.lower() == 'cancel':
                await ctx.send("Configuration canceled.")
                return
            if msg.content.lower() == 'no':
                await ctx.send("Please upload the custom **welcome image** now:")
                try:
                    image_msg = await self.bot.wait_for('message', timeout=120.0, check=check)
                    if image_msg.content.lower() == 'cancel':
                        await ctx.send("Configuration canceled.")
                        return
                    if image_msg.attachments:
                        welcome_image_url = image_msg.attachments[0].url
                    else:
                        await ctx.send("No image detected. Using default image.")
                        welcome_image_url = None
                except asyncio.TimeoutError:
                    await ctx.send("You took too long to upload the image. Using default image.")
                    welcome_image_url = None
            else:
                welcome_image_url = None  # Use default image
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Using default image.")
            welcome_image_url = None

        # Goodbye Image
        await ctx.send("Do you want to use the **default goodbye image**? Please note that you should not delete the uploaded photos for this item, otherwise the feature will use the available image set by default. Type `yes` or `no`:")
        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
            if msg.content.lower() == 'cancel':
                await ctx.send("Configuration canceled.")
                return
            if msg.content.lower() == 'no':
                await ctx.send("Please upload the custom **goodbye image** now:")
                try:
                    image_msg = await self.bot.wait_for('message', timeout=120.0, check=check)
                    if image_msg.content.lower() == 'cancel':
                        await ctx.send("Configuration canceled.")
                        return
                    if image_msg.attachments:
                        goodbye_image_url = image_msg.attachments[0].url
                    else:
                        await ctx.send("No image detected. Using default image.")
                        goodbye_image_url = None
                except asyncio.TimeoutError:
                    await ctx.send("You took too long to upload the image. Using default image.")
                    goodbye_image_url = None
            else:
                goodbye_image_url = None  # Use default image
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Using default image.")
            goodbye_image_url = None

        # Step 5: Embed Hex Color (Optional)
        await ctx.send("**Step 5:** Do you want to set a custom embed hex color? Type the hex code (e.g., `#00ff00`) or `skip` to use default:")
        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
            if msg.content.lower() == 'cancel':
                await ctx.send("Configuration canceled.")
                return
            if msg.content.lower() != 'skip':
                color_input = msg.content.strip()
                # Validate hex color code
                if re.match(r'^#([A-Fa-f0-9]{6})$', color_input):
                    embed_color = int(color_input[1:], 16)
                else:
                    await ctx.send("Invalid hex color code. Using default color.")
                    embed_color = None
            else:
                embed_color = None  # Use default color
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Using default color.")
            embed_color = None

        # Step 6: Preview and Confirmation
        # Create a preview of the welcome message
        preview_embed = discord.Embed(
            title=welcome_title,
            description=welcome_description.replace("{mention}", ctx.author.mention),
            color=embed_color if embed_color is not None else discord.Color.green()
        )
        preview_embed.set_author(
            name=str(ctx.author),
            icon_url=ctx.author.display_avatar.url
        )
        if welcome_image_url:
            preview_embed.set_image(url=welcome_image_url)
        else:
            # Use a default image if available
            image_path = self.get_random_image("assets/welcome")
            if image_path:
                # Note: Since we cannot send local files via URL, we'll skip the image in the preview.
                pass

        # Send preview
        await ctx.send("Here's a preview of your custom **welcome message**:")
        await ctx.send(embed=preview_embed)

        # Ask for confirmation
        await ctx.send("If everything looks good, type `done` to save the changes. Type `cancel` to abort.")
        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
            if msg.content.lower() == 'done':
                # Save the settings
                async with self.lock:
                    self.guild_settings[guild_id]['custom_welcome'] = {
                        'title': welcome_title,
                        'description': welcome_description,
                        'image_url': welcome_image_url,
                        'embed_color': embed_color
                    }
                    self.guild_settings[guild_id]['custom_goodbye'] = {
                        'title': goodbye_title,
                        'description': goodbye_description,
                        'image_url': goodbye_image_url,
                        'embed_color': embed_color
                    }
                    self.guild_settings[guild_id]['custom_new_account_message'] = new_account_description
                    self.save_guild_settings()
                await ctx.send("Your custom messages have been saved and will be used from now on.")
            else:
                await ctx.send("Configuration canceled.")
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Configuration canceled.")


# Event listener for welcoming new members with embed, GIF, and detecting new accounts
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if guild_id in self.guild_settings and "greet_channel" in self.guild_settings[guild_id]:
            channel_id = self.guild_settings[guild_id]["greet_channel"]
            channel = self.bot.get_channel(channel_id)
            if channel:
                permissions = channel.permissions_for(member.guild.me)
                if not permissions.send_messages or not permissions.embed_links:
                    return  # Exit if the bot can't send messages or embed links

                # Use custom message if available
                custom_welcome = self.guild_settings[guild_id].get('custom_welcome')
                if custom_welcome:
                    title = custom_welcome['title']
                    description = custom_welcome['description'].format(
                        mention=member.mention,
                        name=member.name,
                        server=member.guild.name,
                        member_count=member.guild.member_count
                    )
                    image_url = custom_welcome['image_url']
                    embed_color = custom_welcome['embed_color']
                else:
                    # Use default
                    title = "👋 Welcome!"
                    description = random.choice(self.default_greet_messages).format(mention=member.mention)
                    image_url = None
                    embed_color = discord.Color.green()

                embed = discord.Embed(
                    title=title,
                    description=description,
                    color=embed_color if embed_color is not None else discord.Color.green()
                )
                embed.set_author(
                    name=str(member),
                    icon_url=member.display_avatar.url
                )
                embed.set_footer(text=f"User ID: {member.id}")

                # Check if the account is new (e.g., created within the last 7 days)
                account_age = utcnow() - member.created_at
                if account_age.total_seconds() < 7 * 24 * 3600:  # Less than 7 days
                    if account_age.days == 0:
                        hours, remainder = divmod(account_age.seconds, 3600)
                        minutes, _ = divmod(remainder, 60)
                        age_str = f"{hours} hours and {minutes} minutes"
                    else:
                        age_str = f"{account_age.days} days"
                    # Use custom new account message if available
                    new_account_description = self.guild_settings[guild_id].get('custom_new_account_message')
                    if new_account_description:
                        new_account_message = new_account_description.format(
                            mention=member.mention,
                            name=member.name,
                            age=age_str,
                            server=member.guild.name
                        )
                    else:
                        new_account_message = (
                            f"⚠️ {member.mention} has joined, but their account is quite new "
                            f"(created {age_str} ago)."
                        )
                    embed.add_field(name="New Account Detected", value=new_account_message, inline=False)   

                # Set image
                if image_url:
                    embed.set_image(url=image_url)
                    await channel.send(embed=embed)
                else:
                    # Use default image
                    image_path = self.get_random_image("assets/welcome")
                    if image_path:
                        with open(image_path, "rb") as image_file:
                            file = discord.File(image_file, filename=os.path.basename(image_path))
                            embed.set_image(url=f"attachment://{os.path.basename(image_path)}")
                            await channel.send(embed=embed, file=file)
                    else:
                        await channel.send(embed=embed)

    # Test command to simulate both new account and not new account scenarios
    @commands.command(name="testnewaccount")
    @commands.is_owner()
    async def test_new_account(self, ctx, is_new_account: bool):
        member = ctx.author  # Using the command author as the test member
        channel = ctx.channel
        guild_id = str(ctx.guild.id)

        # Simulate account creation date based on is_new_account flag
        if is_new_account:
            simulated_created_at = utcnow() - timedelta(days=1)  # New account (1 day old)
        else:
            simulated_created_at = utcnow() - timedelta(days=30)  # Not a new account (30 days old)

        # Calculate account age using the simulated created_at
        account_age = utcnow() - simulated_created_at

        # Use custom message if available
        custom_welcome = self.guild_settings.get(guild_id, {}).get('custom_welcome')
        if custom_welcome:
            title = custom_welcome['title']
            description = custom_welcome['description'].format(
                mention=member.mention,
                name=member.name,
                server=member.guild.name,
                member_count=member.guild.member_count
            )
            image_url = custom_welcome['image_url']
            embed_color = custom_welcome['embed_color']
        else:
            # Use default
            title = "👋 Welcome!"
            description = random.choice(self.default_greet_messages).format(mention=member.mention)
            image_url = None
            embed_color = discord.Color.green()

        # Create the embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=embed_color if embed_color is not None else discord.Color.green()
        )
        embed.set_author(
            name=str(member),
            icon_url=member.display_avatar.url
        )
        embed.set_footer(text=f"User ID: {member.id}")

        # Append the new account message to the embed if it's a new account
        # Use the simulated account age
        if account_age.total_seconds() < 7 * 24 * 3600:  # Less than 7 days
            if account_age.days == 0:
                hours, remainder = divmod(account_age.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                age_str = f"{hours} hours and {minutes} minutes"
            else:
                age_str = f"{account_age.days} days"
            # Use custom new account message if available
            new_account_description = self.guild_settings.get(guild_id, {}).get('custom_new_account_message')
            if new_account_description:
                new_account_message = new_account_description.format(
                    mention=member.mention,
                    name=member.name,
                    age=age_str,
                    server=member.guild.name
                )
            else:
                new_account_message = (
                    f"⚠️ {member.mention} has joined, but their account is quite new "
                    f"(created {age_str} ago)."
                )
            embed.add_field(name="New Account Detected", value=new_account_message, inline=False)

        # Set image
        if image_url:
            embed.set_image(url=image_url)
            await channel.send(embed=embed)
        else:
            # Use default image
            image_path = self.get_random_image("assets/welcome")
            if image_path:
                with open(image_path, "rb") as image_file:
                    file = discord.File(image_file, filename=os.path.basename(image_path))
                    embed.set_image(url=f"attachment://{os.path.basename(image_path)}")
                    await channel.send(embed=embed, file=file)
            else:
                await channel.send(embed=embed)

     # Modify the on_member_remove method to use custom messages
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if guild_id in self.guild_settings and "goodbye_channel" in self.guild_settings[guild_id]:
            channel_id = self.guild_settings[guild_id]["goodbye_channel"]
            channel = self.bot.get_channel(channel_id)
            if channel:
                permissions = channel.permissions_for(member.guild.me)
                if not permissions.send_messages or not permissions.embed_links:
                    return  # Exit if the bot can't send messages or embed links

                # Use custom message if available
                custom_goodbye = self.guild_settings[guild_id].get('custom_goodbye')
                if custom_goodbye:
                    title = custom_goodbye['title']
                    description = custom_goodbye['description'].format(
                        name=member.name,
                        server=member.guild.name,
                        member_count=member.guild.member_count
                    )
                    image_url = custom_goodbye['image_url']
                    embed_color = custom_goodbye['embed_color']
                else:
                    # Use default
                    title = "💔 Goodbye!"
                    description = random.choice(self.default_goodbye_messages).format(name=member.name)
                    image_url = None
                    embed_color = discord.Color.red()

                embed = discord.Embed(
                    title=title,
                    description=description,
                    color=embed_color if embed_color is not None else discord.Color.red()
                )
                embed.set_author(
                    name=str(member),
                    icon_url=member.display_avatar.url
                )
                embed.set_footer(text=f"User ID: {member.id}")

                # Set image
                if image_url:
                    embed.set_image(url=image_url)
                    await channel.send(embed=embed)
                else:
                    # Use default image
                    image_path = self.get_random_image("assets/goodbye")
                    if image_path:
                        with open(image_path, "rb") as image_file:
                            file = discord.File(image_file, filename=os.path.basename(image_path))
                            embed.set_image(url=f"attachment://{os.path.basename(image_path)}")
                            await channel.send(embed=embed, file=file)
                    else:
                        await channel.send(embed=embed)
async def setup(bot):
    await bot.add_cog(WelcomeGoodbyeCog(bot))
