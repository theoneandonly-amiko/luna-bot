import discord
from discord.ext import commands
import json
import os
import re
import time
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter
import logging
import re

logger = logging.getLogger(__name__)

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "cogs/data/automod_config.json"
        self.config = {}
        self.spam_tracker = defaultdict(list)
        self.spam_threshold = 5  # Max messages within the interval
        self.spam_interval = 10  # Time window in seconds
        self.mention_threshold = 5  # mentions
        self.image_spam_tracker = defaultdict(list)
        self.image_spam_interval = 10  # seconds
        self.image_spam_threshold = 3  # images
        
        # Mass emoji, newline/character spam detection.
        
        self.emoji_threshold = 6  # Max emojis per message
        self.newline_threshold = 10  # Max newlines per message
        self.char_repeat_threshold = 10  # Max repeated characters
        
        # Violation Escalation
        self.violation_counts = defaultdict(int)
        self.last_violation_time = defaultdict(float)
        self.violation_reset_time = 86400  # 24 hours

        # Log channel id per guild
        self.log_channels = {}
        
        # Load config
        self.load_config()

        # Default settings for automod features
        self.default_settings = {
            "spam_detection": False,
            "mention_spam": False,
            "word_filter": False,
            "caps_filter": False,
            "invite_filter": False,
            "image_spam": False,
            "repeated_text": False,
            "scam_detection": False,
            "emoji_spam": False,
            "newline_spam": False,
            "char_spam": False
        }
        # scam link patterns. Let's see...
        self.scam_patterns = [
            # Discord related scams
            r'discord(?:\.gift|\.egift|\.app|nitro)',
            r'free\s*nitro',
            # Steam scams
            r'steam(?:community|gift|profile|game)',
            # Common scam domains
            r'(?:dlscord|discorde?|steamcommunlty|dlscordgift|discordgift|steamgift)\.(?:com|net|org|gift|ru|gg|app)',
            # Generic prize scams
            r'(?:free|get|claim|limited)\s*(?:gift|prize|money|nitro|game)',
            # Crypto scams
            r'(?:crypto|bitcoin|eth|binance|nft)\s*(?:gift|airdrop|free)',
            # QR code scams
            r'(?:verify|authentication|secure)\s*(?:qr|code)',
            # Common scam phrases
            r'@everyone\s*(?:free|gift|nitro|airdrop)',
            r'first\s*\d+\s*users',
            r'(?:click|check)\s*(?:here|this)\s*to\s*(?:claim|get|receive)'
        ]
        self.scam_regex = re.compile('|'.join(self.scam_patterns), re.IGNORECASE)


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
                    "user_warnings": {}
                }
                self.save_config()
        except Exception:
            logger.exception("Failed to load config:")
            self.config = {
                "word_filter": [],
                "warn_threshold": 3,
                "user_warnings": {}
            }

    def save_config(self):
        """Save the automod configuration."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception:
            logger.exception("Failed to save config:")
            

    def count_emojis(self, content):
        """Count both custom and unicode emojis in a message."""
        # Custom emoji pattern
        custom_emoji = re.findall(r'<a?:[a-zA-Z0-9_]+:\d+>', content)
        # Unicode emoji pattern
        unicode_emoji = re.findall(r'[\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]', content)
        return len(custom_emoji) + len(unicode_emoji)

    def check_char_spam(self, content, threshold):
        """Check for repeated character spam."""
        if not content:
            return False
        # Count consecutive repeated characters
        count = 1
        prev_char = content[0]
        for char in content[1:]:
            if char == prev_char:
                count += 1
                if count >= threshold:
                    return True
            else:
                count = 1
                prev_char = char
        return False

    async def handle_violation(self, message, violation_type, description):
        """Handle violations with escalating punishments."""
        
        # You better not kicking the guild owner lmao.
        if message.author.id == message.guild.owner_id:
            return
        
        current_time = time.time()
        user_id = message.author.id
        
        # Reset violations if last one was more than 24h ago
        if current_time - self.last_violation_time[user_id] > self.violation_reset_time:
            self.violation_counts[user_id] = 0

        self.violation_counts[user_id] += 1
        self.last_violation_time[user_id] = current_time
        count = self.violation_counts[user_id]

        # Delete the offending message
        await message.delete()

        # Prepare the base embed
        embed = discord.Embed(
            title=f"AutoMod: {violation_type}",
            description=description,
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )

        # Apply escalating punishments
        if count == 1:
            # First offense: Warning
            embed.add_field(name="Action", value="Warning issued", inline=False)
            
        elif count == 2:
            # Second offense: 5 minute timeout
            await message.author.timeout(timedelta(minutes=5), reason=f"AutoMod: {violation_type}")
            embed.add_field(name="Action", value="5 minute timeout", inline=False)
            
        elif count == 3:
            # Third offense: 1 hour timeout
            await message.author.timeout(timedelta(hours=1), reason=f"AutoMod: {violation_type}")
            embed.add_field(name="Action", value="1 hour timeout", inline=False)
            
        elif count == 4:
            # Fourth offense: Mute
            mute_role = discord.utils.get(message.guild.roles, name="Muted")
            if mute_role:
                await message.author.add_roles(mute_role, reason=f"AutoMod: {violation_type}")
                embed.add_field(name="Action", value="Muted indefinitely", inline=False)
            
        else:
            # Fifth+ offense: Kick
            await message.author.kick(reason=f"AutoMod: Multiple {violation_type} violations")
            embed.add_field(name="Action", value="Kicked from server", inline=False)

        embed.add_field(name="Violation Count", value=f"{count} violations in 24h", inline=False)
        await message.channel.send(embed=embed)
        await self.log_action(
            message.guild,
            violation_type,
            message.author,
            f"Action taken: {embed.fields[-1].value}\nReason: {description}"
            )

    async def log_action(self, guild, action_type, user, description, color=discord.Color.orange()):
        """Log AutoMod actions to the designated channel."""
        guild_id = str(guild.id)
        if guild_id not in self.log_channels:
            return
            
        log_channel = self.bot.get_channel(self.log_channels[guild_id])
        if not log_channel:
            return
            
        embed = discord.Embed(
            title=f"🛡️ AutoMod: {action_type}",
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
        await log_channel.send(embed=embed)


    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def automod(self, ctx):
        """View or modify AutoMod settings."""
        if ctx.invoked_subcommand is None:
            guild_id = str(ctx.guild.id)
            settings = self.config.get(guild_id, self.default_settings)
            
            embed = discord.Embed(
                title="🛡️ AutoMod Configuration",
                description="Current AutoMod settings for this server:",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            for feature, enabled in settings.items():
                status = "✅ Enabled" if enabled else "❌ Disabled"
                embed.add_field(
                    name=feature.replace('_', ' ').title(),
                    value=status,
                    inline=True
                )
                
            embed.add_field(
                name="Usage",
                value="Use `automod toggle <feature> <on/off>` to toggle features\nUse `automod all <on/off>` to toggle all features",
                inline=False
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            
            await ctx.send(embed=embed)

    @automod.command(name="types")
    @commands.has_permissions(administrator=True)
    async def automod_types(self, ctx):
        """Display available AutoMod feature types."""
        guild_id = str(ctx.guild.id)
        settings = self.config.get(guild_id, self.default_settings.copy())
        embed = discord.Embed(
            title="🛡️ Available AutoMod Feature Types",
            description="Listing all available AutoMod features and their current statuses:",
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )
        for feature in self.default_settings:
            # Get status from config if set, otherwise fallback to default
            status = "✅ Enabled" if settings.get(feature, self.default_settings[feature]) else "❌ Disabled"
            embed.add_field(name=feature.replace('_', ' ').title(), value=status, inline=True)
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)


    @automod.command(name="all")
    @commands.has_permissions(administrator=True)
    async def automod_all(self, ctx, state: str):
        """Enable or disable all AutoMod features."""
        if state.lower() not in ['on', 'off']:
            embed = discord.Embed(
                title="⚠️ Invalid Input",
                description="Please use 'on' or 'off' to toggle features.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            return

        enabled = state.lower() == 'on'
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.config:
            self.config[guild_id] = self.default_settings.copy()
            
        for feature in self.default_settings.keys():
            self.config[guild_id][feature] = enabled
            
        self.save_config()
        
        embed = discord.Embed(
            title="🛡️ AutoMod Updated",
            description=f"All AutoMod features have been {'enabled' if enabled else 'disabled'}.",
            color=discord.Color.brand_green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"Updated by {ctx.author}")
        await ctx.send(embed=embed)

    @automod.command()
    @commands.has_permissions(administrator=True)
    async def toggle(self, ctx, feature: str, state: str):
        """Toggle specific AutoMod features."""
        feature = feature.lower()
        if feature not in self.default_settings:
            features_list = "\n".join(self.default_settings.keys())
            embed = discord.Embed(
                title="⚠️ Invalid Feature",
                description=f"Available features:\n```\n{features_list}```",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            return

        if state.lower() not in ['on', 'off']:
            embed = discord.Embed(
                title="⚠️ Invalid Input",
                description="Please use 'on' or 'off' to toggle features.",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            return

        enabled = state.lower() == 'on'
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.config:
            self.config[guild_id] = self.default_settings.copy()
            
        self.config[guild_id][feature] = enabled
        self.save_config()
        
        embed = discord.Embed(
            title="🛡️ AutoMod Feature Updated",
            description=f"**{feature.replace('_', ' ').title()}** has been {'enabled' if enabled else 'disabled'}.",
            color=discord.Color.brand_green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"Updated by {ctx.author}")
        await ctx.send(embed=embed)

    @commands.group(name="threshold")
    @commands.has_permissions(administrator=True)
    async def threshold(self, ctx):
        """Configure AutoMod thresholds."""
        if ctx.invoked_subcommand is None:
            guild_id = str(ctx.guild.id)
            settings = self.config.get(guild_id, {})
            
            embed = discord.Embed(
                title="🔧 AutoMod Thresholds",
                description="Current threshold settings:",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            thresholds = {
                "Spam Messages": settings.get('spam_threshold', self.spam_threshold),
                "Spam Interval": settings.get('spam_interval', self.spam_interval),
                "Mentions": settings.get('mention_threshold', self.mention_threshold),
                "Caps Percentage": settings.get('caps_percentage', 70),
                "Image Spam": settings.get('image_threshold', self.image_spam_threshold),
                "Emoji Limit": settings.get('emoji_threshold', self.emoji_threshold),
                "Newline Limit": settings.get('newline_threshold', self.newline_threshold),
                "Character Repeat": settings.get('char_repeat_threshold', self.char_repeat_threshold)
            }
            
            for name, value in thresholds.items():
                embed.add_field(name=name, value=str(value), inline=True)
                
            embed.add_field(
                name="Usage",
                value="Use `threshold set <type> <value>` to modify thresholds",
                inline=False
            )
            await ctx.send(embed=embed)

    @threshold.command(name="set")
    @commands.has_permissions(administrator=True)
    async def set_threshold(self, ctx, threshold_type: str, value: int):
        """Set a specific threshold value."""
        valid_types = {
            'spam': ('spam_threshold', 1, 20),
            'interval': ('spam_interval', 5, 30),
            'mentions': ('mention_threshold', 1, 15),
            'caps': ('caps_percentage', 50, 100),
            'images': ('image_threshold', 1, 10),
            'emojis': ('emoji_threshold', 1, 20),
            'newlines': ('newline_threshold', 1, 20),
            'chars': ('char_repeat_threshold', 3, 20)
        }

        if threshold_type not in valid_types:
            types_list = "\n".join(f"• {t}" for t in valid_types.keys())
            embed = discord.Embed(
                title="⚠️ Invalid Threshold Type",
                description=f"Valid types:\n{types_list}",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            return

        config_key, min_val, max_val = valid_types[threshold_type]
        
        if not min_val <= value <= max_val:
            embed = discord.Embed(
                title="⚠️ Invalid Value",
                description=f"Value must be between {min_val} and {max_val}",
                color=discord.Color.orange(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)
            return

        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = self.default_settings.copy()
            
        self.config[guild_id][config_key] = value
        self.save_config()

        embed = discord.Embed(
            title="✅ Threshold Updated",
            description=f"{threshold_type.title()} threshold set to {value}",
            color=discord.Color.brand_green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"Updated by {ctx.author}")
        await ctx.send(embed=embed)


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def automodlog(self, ctx, channel: discord.TextChannel):
        """Set the channel for AutoMod logs."""
        guild_id = str(ctx.guild.id)
        self.log_channels[guild_id] = channel.id
        self.save_config()
        
        embed = discord.Embed(
            title="📝 Log Channel Set",
            description=f"AutoMod logs will be sent to {channel.mention}",
            color=discord.Color.brand_green(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"Set by {ctx.author}")
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

    @commands.Cog.listener()
    async def on_message(self, message):
        """Automod features implemented through message listener."""
        if message.author.bot:
            return
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return  # Ignore messages that are commands
        
        guild_id = str(message.guild.id)
        settings = self.config.get(guild_id, self.default_settings)
        current_time = time.time()
        
        # Mention spam protection
        if settings.get('mention_spam', True):
            mention_count = len(message.mentions) + len(message.role_mentions)
            mention_threshold = settings.get('mention_threshold', self.mention_threshold)
            if mention_count > mention_threshold:
                await self.handle_violation(
                    message,
                    "Excessive Mentions",
                    f"{message.author.mention}, please avoid mentioning too many users or roles."
                )
                return

        # Word filter
        if settings.get('word_filter', True):
            word_filter = self.config.get("word_filter", [])
            for word in word_filter:
                pattern = re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE)
                if pattern.search(message.content):
                    await self.handle_violation(
                        message,
                        "Prohibited Word",
                        f"{message.author.mention}, you used a prohibited word."
                    )
                    return
            
        # Spam detection
        if settings.get('spam_detection', True):
            spam_interval = settings.get('spam_interval', self.spam_interval)
            self.spam_tracker[message.author.id].append(current_time)
            self.spam_tracker[message.author.id] = [
                t for t in self.spam_tracker[message.author.id]
                if current_time - t <= spam_interval
            ]
            spam_threshold = settings.get('spam_threshold', self.spam_threshold)
            if len(self.spam_tracker[message.author.id]) > spam_threshold:
                await self.handle_violation(
                    message,
                    "Message Spam",
                    f"{message.author.mention}, please stop spamming."
                )
                return

        # Caps filter
        if settings.get('caps_filter', True):
            caps_count = sum(1 for c in message.content if c.isupper())
            caps_percentage = settings.get('caps_percentage', 70)
            if len(message.content) > 10 and (caps_count / len(message.content)) * 100 > caps_percentage:
                await self.handle_violation(
                    message,
                    "Excessive Caps",
                    f"{message.author.mention}, please avoid using excessive capital letters."
                )
                return

        # Invite link detection
        if settings.get('invite_filter', True):
            invite_pattern = re.compile(r'discord(?:\.gg|app\.com/invite)/[\w-]+')
            if invite_pattern.search(message.content):
                await self.handle_violation(
                    message,
                    "Invite Link",
                    f"{message.author.mention}, please do not post invite links."
                )
                return

        # Image spam detection
        if settings.get('image_spam', True):
            if len(message.attachments) > 0:
                self.image_spam_tracker[message.author.id].append(current_time)
                image_interval = settings.get('image_interval', self.image_spam_interval)
                self.image_spam_tracker[message.author.id] = [
                    t for t in self.image_spam_tracker[message.author.id]
                    if current_time - t <= image_interval
                ]
                image_threshold = settings.get('image_threshold', self.image_spam_threshold)
                if len(self.image_spam_tracker[message.author.id]) > image_threshold:
                    await self.handle_violation(
                        message,
                        "Image Spam",
                        f"{message.author.mention}, please stop spamming images."
                    )
                    return

        # Emoji spam detection
        if settings.get('emoji_spam', True):
            emoji_count = self.count_emojis(message.content)
            emoji_threshold = settings.get('emoji_threshold', self.emoji_threshold)
            if emoji_count > emoji_threshold:
                await self.handle_violation(
                    message,
                    "Emoji Spam",
                    f"{message.author.mention}, please use fewer emojis."
                )
                return

        # Newline spam detection
        if settings.get('newline_spam', True):
            newline_count = message.content.count('\n')
            newline_threshold = settings.get('newline_threshold', self.newline_threshold)
            if newline_count > newline_threshold:
                await self.handle_violation(
                    message,
                    "Newline Spam",
                    f"{message.author.mention}, please use fewer line breaks."
                )
                return

        # Character spam detection
        if settings.get('char_spam', True):
            char_threshold = settings.get('char_repeat_threshold', self.char_repeat_threshold)
            if self.check_char_spam(message.content, char_threshold):
                await self.handle_violation(
                    message,
                    "Character Spam",
                    f"{message.author.mention}, please avoid repeating characters."
                )
                return

        # Repeated text detection
        if settings.get('repeated_text', True):
            words = message.content.split()
            if len(words) > 5:
                word_counts = Counter(words)
                most_common_word, count = word_counts.most_common(1)[0]
                word_repeat_threshold = settings.get('word_repeat_threshold', 5)
                if count > word_repeat_threshold and (count / len(words)) > 0.5:
                    await self.handle_violation(
                        message,
                        "Repeated Text",
                        f"{message.author.mention}, please avoid repeating the same word or phrase excessively."
                    )
                    return

        # Scam detection with comprehensive patterns
        if settings.get('scam_detection', True):
            if self.scam_regex.search(message.content):
                await self.handle_violation(
                    message,
                    "Potential Scam",
                    f"{message.author.mention}, your message was flagged as a potential scam."
                )
                return

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
