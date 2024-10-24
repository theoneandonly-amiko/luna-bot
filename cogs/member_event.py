import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import json
import os
import random

class WelcomeGoodbyeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings_file = "cogs/data/guild_settings.json"
        self.guild_settings = self.load_guild_settings()

        # Randomized welcome and goodbye messages
        self.greet_messages = [
            "Welcome to the server, {mention}! 🎉",
            "Hey {mention}, glad you joined us! 😊",
            "{mention}, we hope you have a great time here! ✨",
            "Hooray! {mention} is here! 🙌",
            "Look who just joined! Welcome, {mention}! 🎊"
        ]
        
        self.goodbye_messages = [
            "Goodbye {name}, we will miss you! 😢",
            "{name} just left the server. Take care! 💔",
            "It was great having you with us, {name}. See you soon! 🌟",
            "{name}, we hope to see you again! 👋",
            "Sad to see you go, {name}. Until next time! 😥"
        ]

    # Load guild settings from a JSON file
    def load_guild_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        return {}

    # Save guild settings to a JSON file
    def save_guild_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.guild_settings, f, indent=4)

    # Helper method to set the welcome channel
    @commands.command(name="setgreetchannel")
    @commands.has_permissions(administrator=True)
    async def set_greet_channel(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            await ctx.send("Please mention a valid channel or provide a channel ID. Example: `!setgreetchannel #welcome`.")
            return

        guild_id = str(ctx.guild.id)
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {}
        self.guild_settings[guild_id]["greet_channel"] = channel.id
        self.save_guild_settings()  # Save after setting
        await ctx.send(f"Greeting channel set to {channel.mention}")

    # Helper method to set the goodbye channel
    @commands.command(name="setgoodbyechannel")
    @commands.has_permissions(administrator=True)
    async def set_goodbye_channel(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            await ctx.send("Please mention a valid channel or provide a channel ID. Example: `!setgoodbyechannel #goodbye`.")
            return

        guild_id = str(ctx.guild.id)
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {}
        self.guild_settings[guild_id]["goodbye_channel"] = channel.id
        self.save_guild_settings()  # Save after setting
        await ctx.send(f"Goodbye channel set to {channel.mention}")

    # Event listener for welcoming new members with embed and GIF

# Event listener for welcoming new members with embed, GIF, and detecting new accounts
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if guild_id in self.guild_settings and "greet_channel" in self.guild_settings[guild_id]:
            channel_id = self.guild_settings[guild_id]["greet_channel"]
            channel = self.bot.get_channel(channel_id)
            if channel:
                message = random.choice(self.greet_messages).format(mention=member.mention)

                embed = discord.Embed(
                    title="👋 Welcome!",
                    description=message,
                    color=discord.Color.green()
                )
                embed.set_author(
                    name=str(member),
                    icon_url=member.avatar.url
                )
                embed.set_footer(text=f"User ID: {member.id}")

                # Check if the account is new (e.g., account created within the last 7 days)
                account_age = datetime.now(timezone.utc) - member.created_at
                if account_age.days < 7:
                    # Append the new account message to the embed
                    new_account_message = f"⚠️ {member.mention} has joined, but their account is quite new (created {account_age.days} days ago)."
                    embed.add_field(name="New Account Detected", value=new_account_message, inline=False)

                # Load the welcome GIF from assets
                gif_path = "assets/welcome/welcome.gif"
                if os.path.exists(gif_path):
                    with open(gif_path, "rb") as gif_file:
                        file = discord.File(gif_file, filename="welcome.gif")
                        embed.set_image(url="attachment://welcome.gif")
                        await channel.send(embed=embed, file=file)
                else:
                    await channel.send(embed=embed)

    # Test command to simulate both new account and not new account scenarios
    @commands.command(name="testnewaccount")
    @commands.is_owner()
    async def test_new_account(self, ctx, is_new_account: bool):
        member = ctx.author  # Using the command author as the test member
        channel = ctx.channel

        # Simulate account creation date based on is_new_account flag
        if is_new_account:
            created_at = datetime.now(timezone.utc) - timedelta(days=1)  # New account (1 day old)
        else:
            created_at = datetime.now(timezone.utc) - timedelta(days=30)  # Not a new account (30 days old)

        account_age = datetime.now(timezone.utc) - created_at

        message = random.choice(self.greet_messages).format(mention=member.mention)

        embed = discord.Embed(
            title="👋 Welcome (Test)!",
            description=message,
            color=discord.Color.green()
        )
        embed.set_author(
            name=str(member),
            icon_url=member.avatar.url
        )
        embed.set_footer(text=f"User ID: {member.id}")

        # Append the new account message to the embed if it's a new account
        if account_age.days < 7:
            new_account_message = f"⚠️ {member.mention} has joined, but their account is quite new (created {account_age.days} days ago)."
            embed.add_field(name="New Account Detected (Test)", value=new_account_message, inline=False)

        # Simulate sending a welcome message
        await channel.send(embed=embed)

    # Event listener for saying goodbye to members with embed and GIF
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild_id = str(member.guild.id)
        if guild_id in self.guild_settings and "goodbye_channel" in self.guild_settings[guild_id]:
            channel_id = self.guild_settings[guild_id]["goodbye_channel"]
            channel = self.bot.get_channel(channel_id)
            if channel:
                permissions = channel.permissions_for(member.guild.me)
                if not permissions.send_messages or not permissions.embed_links:
                    return  # Exit if the bot can't send messages
                message = random.choice(self.goodbye_messages).format(name=member.name)

                embed = discord.Embed(
                    title="💔 Goodbye!",
                    description=message,
                    color=discord.Color.red()
                )
                embed.set_author(
                    name=str(member),
                    icon_url=member.avatar.url
                )
                embed.set_footer(text=f"User ID: {member.id}")

                # Load the goodbye GIF from assets
                gif_path = "assets/goodbye/goodbye.gif"
                if os.path.exists(gif_path):
                    with open(gif_path, "rb") as gif_file:
                        file = discord.File(gif_file, filename="goodbye.gif")
                        embed.set_image(url="attachment://goodbye.gif")
                        await channel.send(embed=embed, file=file)
                else:
                    await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(WelcomeGoodbyeCog(bot))
