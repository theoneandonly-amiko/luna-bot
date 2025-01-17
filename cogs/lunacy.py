import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
from discord import app_commands
import random
import asyncio
import sqlite3
import os
from typing import Optional
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager

class Lunacy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.currency_name = "Luna"
        self.db_path = "cogs/data/lunacy.db"
        self.default_items = [
                    ("Moon Badge", 5000, "A shiny badge with a crescent moon | +5% daily rewards", "daily_bonus", 0.05),
                    ("Star Compass", 15000, "Points to the brightest star | +10% work earnings", "work_bonus", 0.10),
                    ("Lunar Crown", 50000, "A crown fit for lunar royalty | +15% to all earnings", "all_bonus", 0.15),
                    ("Cosmic Quill", 12000, "Writes with starlight ink | +8% trade limits", "trade_bonus", 0.08),
                    ("Nebula Necklace", 25000, "Contains swirling cosmic dust | +12% gamble wins", "gamble_bonus", 0.12),
                    ("Stellar Shield", 75000, "Protection forged from meteorites | +20% all earnings", "all_bonus", 0.20),
                    ("Moonstone Ring", 35000, "Glows during full moons | +15% daily rewards", "daily_bonus", 0.15),
                    ("Astral Map", 45000, "Shows hidden constellations | +18% work earnings", "work_bonus", 0.18),
                    ("Galaxy Globe", 100000, "A miniature universe in glass | +25% all earnings", "all_bonus", 0.25),
                    ("Comet Shard", 20000, "Still warm from its journey | +10% gamble wins", "gamble_bonus", 0.10),
                    ("Star Whistle", 18000, "Plays celestial melodies | +12% trade limits", "trade_bonus", 0.12),
                    ("Luna's Blessing", 150000, "A rare blessing from the moon itself | +30% all earnings", "all_bonus", 0.30),
                    ("Void Crystal", 80000, "Captures darkness between stars | +22% gamble wins", "gamble_bonus", 0.22),
                    ("Solar Flare Flask", 40000, "Contains bottled sunlight | +20% work earnings", "work_bonus", 0.20),
                    ("Constellation Charm", 30000, "Changes pattern with seasons | +15% daily rewards", "daily_bonus", 0.15),
                    ("Meteor Bracelet", 60000, "Crafted from fallen stars | +18% gamble wins", "gamble_bonus", 0.18),
                    ("Celestial Hourglass", 70000, "Measures time between worlds | +22% daily rewards", "daily_bonus", 0.22),
                    ("Quantum Lens", 85000, "Views parallel universes | +25% work earnings", "work_bonus", 0.25),
                    ("Gravity Well", 95000, "Bends space itself | +28% trade limits", "trade_bonus", 0.28),
                    ("Dark Matter Relic", 120000, "Contains invisible energy | +32% all earnings", "all_bonus", 0.32)
                ]
        self.limited_items = [
            ("Lunar Eclipse Pendant", 100000, "A rare pendant that glows during eclipses | +35% all earnings", True, "all_bonus", 0.35),
            ("Stardust Potion", 75000, "Bottled stardust that sparkles eternally | +40% work earnings", True, "work_bonus", 0.40),
            ("Cosmic Dice", 90000, "Dice made from meteorite fragments | +45% gamble wins", True, "gamble_bonus", 0.45),
            ("Nebula Crystal", 150000, "Contains swirling colors of a distant nebula | +50% daily rewards", True, "daily_bonus", 0.50),
            ("Celestial Compass", 200000, "Points to the nearest star system | +55% all earnings", True, "all_bonus", 0.55),
            ("Moonlight Feather", 95000, "A feather that shimmers with lunar energy | +42% work earnings", True, "work_bonus", 0.42),
            ("Star Fragment", 85000, "A piece of a fallen star | +40% daily rewards", True, "daily_bonus", 0.40),
            ("Void Essence", 250000, "Pure darkness captured in a bottle | +60% gamble wins", True, "gamble_bonus", 0.60),
            ("Galaxy Pearl", 300000, "Contains an entire miniature galaxy | +65% all earnings", True, "all_bonus", 0.65),
            ("Aurora Crown", 350000, "Changes colors like the northern lights | +70% all earnings", True, "all_bonus", 0.70),
            ("Cosmic Map", 120000, "Shows undiscovered constellations | +45% work earnings", True, "work_bonus", 0.45),
            ("Meteor Shard", 110000, "Still warm from entering the atmosphere | +43% gamble wins", True, "gamble_bonus", 0.43),
            ("Supernova Scepter", 400000, "Channels the power of dying stars | +75% all earnings", True, "all_bonus", 0.75),
            ("Black Hole Pearl", 450000, "Dense with infinite potential | +80% all earnings", True, "all_bonus", 0.80),
            ("Time Crystal", 280000, "Frozen moments of eternity | +65% daily rewards", True, "daily_bonus", 0.65),
            ("Quantum Prism", 320000, "Splits reality into possibilities | +70% work earnings", True, "work_bonus", 0.70),
            ("Stellar Core", 380000, "The heart of a star | +75% gamble wins", True, "gamble_bonus", 0.75),
            ("Cosmic Chalice", 290000, "Holds the essence of space | +68% daily rewards", True, "daily_bonus", 0.68),
            ("Astral Crown", 420000, "Worn by cosmic royalty | +78% all earnings", True, "all_bonus", 0.78),
            ("Void Walker's Stone", 360000, "Step through space and time | +72% work earnings", True, "work_bonus", 0.72)
        ]

        self.default_achievements = [
            ("Moon Walker", "Reach 10,000 Luna balance", 5000, 10000),
            ("Lunar Millionaire", "Reach 1,000,000 Luna balance", 50000, 1000000),
            ("Stellar Trader", "Complete 50 trades", 10000, 50),
            ("Trade Mogul", "Complete 200 trades", 25000, 200),
            ("Lucky Star", "Win 25 gambles", 7500, 25),
            ("Fortune's Favorite", "Win 100 gambles", 20000, 100),
            ("Dedicated Explorer", "Maintain a 7-day streak", 15000, 7),
            ("Lunar Devotee", "Maintain a 30-day streak", 50000, 30),
            ("Shopkeeper's Friend", "Buy 50 items from shop", 5000, 50),
            ("Collection Master", "Own one of each shop item", 30000, 1),
            ("Work Ethic", "Complete work command 100 times", 10000, 100),
            ("Luna Tycoon", "Earn 5,000,000 total Luna", 100000, 5000000),
                            # New Work Achievements
            ("Cosmic Employee", "Complete 25 work shifts", 3000, 25),
            ("Star Supervisor", "Complete 50 work shifts", 7500, 50),
            ("Galactic Manager", "Complete 150 work shifts", 15000, 150),
            ("Celestial CEO", "Complete 500 work shifts", 50000, 500),
            ("Space Pioneer", "Earn 100,000 Luna from work", 10000, 100000),
            ("Stellar Tycoon", "Earn 1,000,000 Luna from work", 75000, 1000000),
            
                                # New Shop Achievements
            ("Cosmic Collector", "Own 5 different shop items", 5000, 5),
            ("Stellar Shopper", "Own 10 different shop items", 15000, 10),
            ("Galactic Curator", "Own 15 different shop items", 30000, 15),
            ("Limited Edition Hunter", "Buy 3 limited items", 25000, 3),
            ("Rare Treasure Seeker", "Buy 10 limited items", 75000, 10),
            ("Master Merchant", "Spend 1,000,000 Luna in shop", 50000, 1000000),
            
                                # New Gambling Achievements
            ("Risk Taker", "Gamble 50 times", 5000, 50),
            ("High Roller", "Gamble 200 times", 20000, 200),
            ("Cosmic Gambler", "Gamble 1000 times", 100000, 1000),
            ("Lucky Streak", "Win 5 gambles in a row", 25000, 5),
                                # New Trading Achievements
            ("Trade Apprentice", "Complete 25 trades", 5000, 25),
            ("Market Maven", "Complete 100 trades", 15000, 100),
            ("Trading Legend", "Complete 500 trades", 75000, 500),
                        
                            # New Balance Milestones
            ("Star Gazer", "Reach 50,000 Luna balance", 7500, 50000),
            ("Nebula Navigator", "Reach 500,000 Luna balance", 25000, 500000),
            ("Galaxy Guardian", "Reach 5,000,000 Luna balance", 150000, 5000000),
            ("Universal Emperor", "Reach 10,000,000 Luna balance", 300000, 10000000)
        ]

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.setup_database()
        self.initialize_shop()  # Add this line
        self.rotate_shop_items.start()  # Start the task for limited items

    def setup_database(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            # Create version tracking
            c.execute('''CREATE TABLE IF NOT EXISTS db_version 
                        (version INTEGER PRIMARY KEY, 
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

            # Get current version
            c.execute('SELECT version FROM db_version')
            current_version = c.fetchone()
            
            if not current_version:
                c.execute('INSERT INTO db_version (version, updated_at) VALUES (0, CURRENT_TIMESTAMP)')
                current_version = (0,)

            # Version 1: Initial tables
            if current_version[0] < 1:
                c.execute('''CREATE TABLE IF NOT EXISTS users 
                        (user_id TEXT PRIMARY KEY, 
                        balance INTEGER DEFAULT 0, 
                        last_daily TIMESTAMP,
                        streak INTEGER DEFAULT 0,
                        work_count INTEGER DEFAULT 0,
                        work_earnings INTEGER DEFAULT 0,
                        trades_completed INTEGER DEFAULT 0,
                        items_bought INTEGER DEFAULT 0,
                        limited_items_bought INTEGER DEFAULT 0,
                        total_spent INTEGER DEFAULT 0,
                        total_gambles INTEGER DEFAULT 0,
                        gamble_wins INTEGER DEFAULT 0)''')

                c.execute('''CREATE TABLE IF NOT EXISTS achievements
                            (id INTEGER PRIMARY KEY, 
                            name TEXT UNIQUE, 
                            description TEXT, 
                            reward INTEGER, 
                            requirement INTEGER)''')
                
                c.execute('''CREATE TABLE IF NOT EXISTS user_achievements
                            (user_id TEXT, 
                            achievement_id INTEGER,
                            completed_at TIMESTAMP,
                            FOREIGN KEY(user_id) REFERENCES users(user_id),
                            FOREIGN KEY(achievement_id) REFERENCES achievements(id),
                            UNIQUE(user_id, achievement_id))''')

                c.execute('''CREATE TABLE IF NOT EXISTS shop
                            (item_id INTEGER PRIMARY KEY, 
                            name TEXT, 
                            price INTEGER,
                            description TEXT, 
                            limited BOOLEAN DEFAULT FALSE,
                            available_until TIMESTAMP,
                            stock_limit INTEGER DEFAULT NULL)''')

                c.execute('''CREATE TABLE IF NOT EXISTS perks
                            (id INTEGER PRIMARY KEY,
                            name TEXT,
                            description TEXT,
                            effect_type TEXT,
                            effect_value FLOAT,
                            price INTEGER,
                            duration INTEGER)''')

                c.execute('''CREATE TABLE IF NOT EXISTS user_perks
                            (user_id TEXT,
                            perk_id INTEGER,
                            acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP,
                            FOREIGN KEY(user_id) REFERENCES users(user_id),
                            FOREIGN KEY(perk_id) REFERENCES perks(id))''')

                # Insert default achievements with UNIQUE constraint handling
                
                c.executemany('''INSERT OR IGNORE INTO achievements (name, description, reward, requirement)
                                VALUES (?, ?, ?, ?)''', self.default_achievements)
                
                c.execute('UPDATE db_version SET version = 1')

            # Version 2: Add inventory with UNIQUE constraint
            if current_version[0] < 2:
                # Create temporary table with new structure
                c.execute('''CREATE TABLE IF NOT EXISTS inventory_new
                            (user_id TEXT, 
                            item_id INTEGER, 
                            quantity INTEGER,
                            acquired_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(user_id) REFERENCES users(user_id),
                            FOREIGN KEY(item_id) REFERENCES shop(item_id),
                            UNIQUE(user_id, item_id))''')
                
                # Migrate existing data if inventory table exists
                c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory'")
                if c.fetchone():
                    c.execute('''INSERT OR REPLACE INTO inventory_new (user_id, item_id, quantity)
                                SELECT user_id, item_id, quantity FROM inventory''')
                    c.execute('DROP TABLE inventory')
                
                c.execute('ALTER TABLE inventory_new RENAME TO inventory')
                c.execute('UPDATE db_version SET version = 2')

            # Version 3: Add transaction history
            if current_version[0] < 3:
                c.execute('''CREATE TABLE IF NOT EXISTS transactions
                            (id INTEGER PRIMARY KEY,
                            user_id TEXT,
                            type TEXT,
                            amount INTEGER,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            details TEXT,
                            FOREIGN KEY(user_id) REFERENCES users(user_id))''')
                
                c.execute('UPDATE db_version SET version = 3')

            # Version 4: Add perk support to shop and inventory
            if current_version[0] < 4:
                # Check if columns exist before adding them
                c.execute("PRAGMA table_info(shop)")
                columns = [column[1] for column in c.fetchall()]
                
                if 'perk_type' not in columns:
                    c.execute('ALTER TABLE shop ADD COLUMN perk_type TEXT DEFAULT NULL')
                if 'perk_value' not in columns:
                    c.execute('ALTER TABLE shop ADD COLUMN perk_value FLOAT DEFAULT 0')
                
                # Add active_effects table to track combined bonuses
                c.execute('''CREATE TABLE IF NOT EXISTS active_effects
                            (user_id TEXT,
                            effect_type TEXT,
                            total_bonus FLOAT,
                            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(user_id) REFERENCES users(user_id),
                            UNIQUE(user_id, effect_type))''')
                
                # Update version
                c.execute('UPDATE db_version SET version = 4')
            # Version 5: Add new items without affecting existing data
            if current_version[0] < 5:
                # Get existing items
                c.execute('SELECT name FROM shop WHERE limited = FALSE')
                existing_items = {row[0] for row in c.fetchall()}
                
                # Add only new items that don't exist
                for item in self.default_items:
                    if item[0] not in existing_items:
                        c.execute('''INSERT INTO shop (name, price, description, perk_type, perk_value, limited) 
                                    VALUES (?, ?, ?, ?, ?, FALSE)''', item)
                
                # Get existing achievements
                c.execute('SELECT name FROM achievements')
                existing_achievements = {row[0] for row in c.fetchall()}
                
                # Add only new achievements that don't exist
                for achievement in self.default_achievements:
                    if achievement[0] not in existing_achievements:
                        c.execute('''INSERT INTO achievements (name, description, reward, requirement)
                                    VALUES (?, ?, ?, ?)''', achievement)
                
                c.execute('UPDATE db_version SET version = 5')
                

            conn.commit()

    def calculate_user_bonus(self, user_id: str, bonus_type: str) -> float:
        with self.db_transaction() as c:
            c.execute('''SELECT SUM(s.perk_value)
                        FROM inventory i
                        JOIN shop s ON i.item_id = s.item_id
                        WHERE i.user_id = ? AND 
                        (s.perk_type = ? OR s.perk_type = 'all_bonus')''', 
                    (user_id, bonus_type))
            total_bonus = c.fetchone()[0] or 0
        return total_bonus

    def initialize_shop(self):
        with self.db_transaction() as c:
            c.execute('SELECT COUNT(*) FROM shop WHERE limited = FALSE')
            if c.fetchone()[0] == 0:
                c.executemany('''INSERT INTO shop (name, price, description, perk_type, perk_value, limited) 
                                VALUES (?, ?, ?, ?, ?, FALSE)''', self.default_items)


    def format_perk_display(self, perk_type: str, perk_value: float) -> str:
        if not perk_type:
            return "No bonus"
        bonus_type = perk_type.replace('_', ' ')
        return f"+{int(perk_value*100)}% {bonus_type}"


    def check_achievement_progress(self, user_id: str, achievement_type: str, value: int):
        with self.db_transaction() as c:
            # Get relevant achievements for the type
            c.execute('''SELECT id, name, description, reward, requirement 
                        FROM achievements 
                        WHERE description LIKE ?''', (f"%{achievement_type}%",))
            achievements = c.fetchall()
            
            rewards_earned = 0
            for ach_id, name, desc, reward, req in achievements:
                # Check if already completed
                c.execute('''SELECT completed_at FROM user_achievements 
                            WHERE user_id = ? AND achievement_id = ?''', 
                        (user_id, ach_id))
                if c.fetchone() is None and value >= req:
                    # Award achievement and update balance in same transaction
                    c.execute('''INSERT INTO user_achievements (user_id, achievement_id, completed_at)
                                VALUES (?, ?, ?)''', 
                            (user_id, ach_id, datetime.now().isoformat()))
                    c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', 
                            (reward, user_id))
                    rewards_earned += reward
                    
            return rewards_earned



    # Helper methods to add at class level
    async def check_funds(self, ctx: commands.Context, amount: int) -> bool:
        """Unified balance checking"""
        user_balance = self.get_balance(str(ctx.author.id))
        if user_balance < amount:
            await ctx.send(f"You don't have enough {self.currency_name}!")
            return False
        return True

    def create_transaction_embed(self, title: str, description: str, color: discord.Color) -> discord.Embed:
        """Unified embed creation"""
        return discord.Embed(
            title=title,
            description=description,
            color=color
        )

    @contextmanager
    def db_transaction(self):
        """Context manager for database transactions"""
        with sqlite3.connect(self.db_path) as conn:
            try:
                yield conn.cursor()
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e


    def format_item_field(self, name: str, price: int = None, description: str = None, quantity: int = None) -> tuple:
        """Unified item formatting for shop and inventory displays"""
        if price:
            title = f"{name} - {price:,} {self.currency_name}"
        else:
            title = f"{name} (x{quantity})"
        return (title, description)

    def calculate_reward(self, base_min: int, base_max: int, bonus_multiplier: float = 0) -> tuple:
        """Unified reward calculation for daily/work rewards"""
        base_amount = random.randint(base_min, base_max)
        final_amount = int(base_amount * (1 + bonus_multiplier))
        return base_amount, final_amount

    def get_balance(self, user_id: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # Start transaction
            c.execute('BEGIN TRANSACTION')
            try:
                # Insert user if not exists
                c.execute('INSERT OR IGNORE INTO users (user_id, balance, last_daily) VALUES (?, 0, NULL)', (user_id,))
                # Get balance
                c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
                balance = c.fetchone()[0]
                # Commit transaction
                conn.commit()
                return balance
            except Exception as e:
                # Rollback transaction if something goes wrong
                conn.rollback()
                raise e



    def update_balance(self, user_id: str, amount: int):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
            conn.commit()
    @tasks.loop(hours=24)
    async def rotate_shop_items(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # Remove expired limited items
            c.execute('DELETE FROM shop WHERE limited = TRUE')
            # Add new random limited items
            selected_items = random.sample(self.limited_items, 2)
            expiry_time = datetime.now() + timedelta(days=1)
            for name, price, desc, limited, perk_type, perk_value in selected_items:
                c.execute('''INSERT INTO shop (name, price, description, limited, available_until, perk_type, perk_value)
                            VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                        (name, price, desc, limited, expiry_time.isoformat(), perk_type, perk_value))
            conn.commit()

    @commands.hybrid_command(name="achievements", description="View your achievements")
    async def achievements(self, ctx: commands.Context):
        with self.db_transaction() as c:
            c.execute('''SELECT a.name, a.description, a.reward, ua.completed_at
                        FROM achievements a
                        LEFT JOIN user_achievements ua 
                        ON a.id = ua.achievement_id AND ua.user_id = ?''', 
                    (str(ctx.author.id),))
            achievements = c.fetchall()

        # Create paginated embeds
        achievements_per_page = 5
        total_achievements = len(achievements)
        total_pages = max(1, (total_achievements + achievements_per_page - 1) // achievements_per_page)
        pages = []
        
        for i in range(0, total_achievements, achievements_per_page):
            embed = discord.Embed(
                title="🏆 Achievements",
                description="Complete tasks to earn rewards!",
                color=discord.Color.gold()
            )
            
            page_achievements = achievements[i:i + achievements_per_page]
            for name, desc, reward, completed_at in page_achievements:
                status = "✅ Completed" if completed_at else "❌ Incomplete"
                embed.add_field(
                    name=f"{name} [{status}]",
                    value=f"{desc}\nReward: {reward:,} {self.currency_name}",
                    inline=False
                )
            
            current_page = i // achievements_per_page + 1
            embed.set_footer(text=f"Page {current_page} of {total_pages}")
            pages.append(embed)

        if pages:
            message = await ctx.send(embed=pages[0])
            if len(pages) > 1:
                await message.add_reaction("⬅️")
                await message.add_reaction("➡️")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"]

                current_page = 0
                while True:
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                        if str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                            current_page += 1
                            await message.edit(embed=pages[current_page])
                        elif str(reaction.emoji) == "⬅️" and current_page > 0:
                            current_page -= 1
                            await message.edit(embed=pages[current_page])

                        await message.remove_reaction(reaction, user)
                    except asyncio.TimeoutError:
                        break

    @commands.hybrid_command(name="balance", description="Check your Luna balance")
    async def balance(self, ctx: commands.Context):
        balance = self.get_balance(str(ctx.author.id))
        embed = discord.Embed(
            title="🌙 Luna Balance",
            description=f"You have **{balance:,}** {self.currency_name}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        
    @commands.hybrid_command(name="daily", description="Collect your daily Luna with streak bonuses!")
    async def daily(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('BEGIN TRANSACTION')
            try:
                c.execute('INSERT OR IGNORE INTO users (user_id, balance, last_daily, streak) VALUES (?, 0, NULL, 0)', (user_id,))
                c.execute('SELECT last_daily, streak FROM users WHERE user_id = ?', (user_id,))
                last_daily, streak = c.fetchone()
                
                if last_daily:
                    last_claim = datetime.fromisoformat(last_daily)
                    time_diff = datetime.now() - last_claim
                    
                    if time_diff < timedelta(days=1):
                        time_left = timedelta(days=1) - time_diff
                        hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        await ctx.send(f"Wait {hours}h {minutes}m {seconds}s before claiming again!")
                        return
                    
                    # Reset streak if more than 48 hours passed
                    if time_diff > timedelta(days=2):
                        streak = 0
                    else:
                        streak += 1
                else:
                    streak = 1

                # Calculate reward based on streak
                base_amount = random.randint(100, 1000)
                streak_bonus = min(streak * 0.1, 1.0)  # Cap bonus at 100%
                
                # Calculate daily bonus from items and apply both bonuses
                daily_bonus = self.calculate_user_bonus(user_id, "daily_bonus")
                final_amount = int(base_amount * (1 + streak_bonus) * (1 + daily_bonus))
                
                c.execute('''UPDATE users 
                            SET balance = balance + ?, 
                                last_daily = ?, 
                                streak = ? 
                            WHERE user_id = ?''', 
                        (final_amount, datetime.now().isoformat(), streak, user_id))
                
                conn.commit()

                embed = discord.Embed(
                    title="🌙 Daily Luna Reward",
                    description=f"**Base Reward:** {base_amount:,} {self.currency_name}\n"
                            f"**Streak Bonus:** +{int(streak_bonus*100)}%\n"
                            f"**Item Bonus:** +{int(daily_bonus*100)}%\n"
                            f"**Final Reward:** {final_amount:,} {self.currency_name}\n"
                            f"**Current Streak:** {streak} days 🔥",
                    color=discord.Color.green()
                )
                rewards = self.check_achievement_progress(user_id, "streak", streak)
                if rewards > 0:
                    embed.add_field(
                        name="🏆 Achievement Unlocked!",
                        value=f"You earned {rewards:,} {self.currency_name} from achievements!"
                    )
                await ctx.send(embed=embed)
                
            except Exception as e:
                conn.rollback()
                raise e


    @commands.hybrid_command(name="leaderboard", description="Show the richest users")
    async def leaderboard(self, ctx: commands.Context):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''SELECT user_id, balance FROM users 
                        ORDER BY balance DESC LIMIT 10''')
            top_users = c.fetchall()

        description = ""
        for i, (user_id, balance) in enumerate(top_users, 1):
            user = await self.bot.fetch_user(int(user_id))
            description += f"{i}. {user.name}: **{balance:,}** {self.currency_name}\n"

        embed = discord.Embed(
            title="🏆 Luna Leaderboard",
            description=description,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="work", description="Work to earn Luna")
    @commands.cooldown(1, 5, commands.BucketType.user)  # 5 seconds cooldown
    async def work(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        
        with self.db_transaction() as c:
            c.execute('''UPDATE users 
                        SET work_count = COALESCE(work_count, 0) + 1,
                        work_earnings = COALESCE(work_earnings, 0)
                        WHERE user_id = ?''', (user_id,))
            
            
            jobs = [
                ("🌟 Stargazer", "watched the stars", 50, 200),
                ("🌙 Moonkeeper", "guarded the moon", 100, 300),
                ("⭐ Constellation Artist", "drew constellations", 150, 400),
                ("🌠 Meteor Counter", "tracked shooting stars", 200, 450),
                ("🪐 Planet Guide", "led tours of the solar system", 250, 500),
                ("🌌 Galaxy Mapper", "charted new galaxies", 300, 600),
                ("💫 Stardust Collector", "gathered cosmic particles", 175, 425),
                ("🔭 Observatory Tech", "maintained the telescopes", 225, 475),
                ("☄️ Comet Tracker", "predicted comet paths", 275, 550),
                ("🌍 Space Weather Reporter", "forecasted solar winds", 150, 375),
                ("🎇 Aurora Photographer", "captured northern lights", 325, 575),
                ("🌑 Eclipse Coordinator", "organized eclipse viewing", 350, 625),
                ("✨ Stellar Cartographer", "mapped star systems", 275, 525),
                ("🛸 UFO Investigator", "documented strange sightings", 400, 700),
                ("🌗 Lunar Photographer", "photographed moon phases", 225, 450),
                ("⚡ Solar Flare Monitor", "tracked solar activity", 300, 550),
                ("🌠 Zodiac Guide", "interpreted star signs", 250, 500),
                ("🎪 Space Carnival Host", "entertained star gazers", 275, 525),
                ("📡 Signal Searcher", "listened for cosmic signals", 350, 650),
                ("🌈 Spectrum Analyzer", "studied starlight colors", 325, 600),
                ("🎨 Nebula Artist", "painted cosmic clouds", 275, 525),
                ("📝 Star Chronicler", "documented celestial events", 300, 575),
                ("🔮 Cosmic Fortune Teller", "read the celestial alignments", 350, 650),
                ("🎭 Space Theater Director", "performed cosmic plays", 400, 700),
                ("🎼 Stellar Musician", "composed space symphonies", 375, 675),
                ("🏃 Asteroid Runner", "delivered messages across space", 425, 725),
                ("🎮 Space Game Designer", "created cosmic simulations", 450, 750),
                ("🎪 Zero-G Acrobat", "performed in space circus", 500, 800),
                ("🌿 Space Botanist", "grew lunar plants", 350, 625),
                ("🍳 Cosmic Chef", "cooked with stellar ingredients", 375, 650),
                ("🎓 Space Academy Teacher", "educated future astronauts", 400, 700),
                ("🎨 Constellation Designer", "created new star patterns", 425, 725),
                ("📚 Cosmic Librarian", "organized stellar archives", 300, 575),
                ("🎭 Space Tour Guide", "led cosmic expeditions", 450, 750),
                ("🔧 Starship Mechanic", "repaired cosmic vessels", 500, 800),
                ("🎪 Zero-G Dancer", "performed space ballet", 475, 775),
                ("🎨 Aurora Sculptor", "shaped northern lights", 525, 825),
                ("📡 Alien Signal Decoder", "translated cosmic messages", 550, 850),
                ("🔬 Dark Matter Researcher", "studied invisible forces", 575, 875),
                ("🎮 Space Race Referee", "judged cosmic competitions", 400, 700),    
                ("🌌 Void Walker", "explored the cosmic abyss", 500, 850),
                ("⚡ Quantum Jumper", "traversed parallel universes", 550, 900),
                ("🎆 Stellar Alchemist", "transmuted cosmic energy", 600, 950),
                ("🌠 Wish Catcher", "collected shooting stars", 450, 800),
                ("🎪 Cosmic Carnival Master", "hosted intergalactic festivals", 525, 875),
                ("🔮 Reality Weaver", "mended space-time fabric", 650, 1000),
                ("💫 Star Shepherd", "guided newborn stars", 475, 825),
                ("🎨 Galaxy Painter", "colored cosmic clouds", 525, 875),
                ("🎭 Celestial Storyteller", "narrated cosmic legends", 400, 750),
                ("🌟 Light Dancer", "performed with starlight", 450, 800),
                ("🎪 Nebula Tamer", "trained cosmic clouds", 575, 925),
                ("🌙 Dream Walker", "patrolled lunar dreamscapes", 500, 850),
                ("⚜️ Stellar Jeweler", "crafted constellation gems", 600, 950),
                ("🎵 Star Singer", "harmonized with celestial spheres", 525, 875),
                ("🌠 Comet Rider", "surfed cosmic streams", 650, 1000),
                ("🎪 Space-Time Acrobat", "danced through dimensions", 575, 925),
                ("🌌 Void Whisperer", "communed with cosmic silence", 625, 975),
                ("💫 Stardust Weaver", "spun cosmic threads", 550, 900),
                ("🎨 Aurora Dancer", "painted with northern lights", 500, 850),
                ("🌟 Light Sculptor", "shaped pure starlight", 600, 950)
            ]


            job = random.choice(jobs)
            base_amount = random.randint(job[2], job[3])
            
            # Calculate work bonus and apply it
            work_bonus = self.calculate_user_bonus(user_id, "work_bonus")
            final_amount = int(base_amount * (1 + work_bonus))
            
            # Update both work earnings and balance
            c.execute('''UPDATE users 
                        SET work_earnings = work_earnings + ?,
                        balance = balance + ?
                        WHERE user_id = ?''', 
                    (final_amount, final_amount, user_id))
            
            # Get updated stats for achievement checking
            c.execute('SELECT work_count, work_earnings FROM users WHERE user_id = ?', (user_id,))
            work_count, total_earnings = c.fetchone()
            
        # Check both work count and earnings achievements
        count_rewards = self.check_achievement_progress(user_id, "work shifts", work_count)
        earnings_rewards = self.check_achievement_progress(user_id, "Luna from work", total_earnings)
        
        embed = discord.Embed(
            title=f"Work - {job[0]}",
            description=f"You {job[1]} and earned **{final_amount:,}** {self.currency_name}!\n"
                    f"Work Bonus: +{int(work_bonus * 100)}%",
            color=discord.Color.green()
        )
        
        total_rewards = count_rewards + earnings_rewards
        if total_rewards > 0:
            embed.add_field(
                name="🏆 Achievement Unlocked!",
                value=f"You earned {total_rewards:,} {self.currency_name} from achievements!"
            )
        await ctx.send(embed=embed)


    @commands.hybrid_command(name="shop", description="View the Luna shop")
    async def shop(self, ctx: Context):
        with self.db_transaction() as c:
            # Get regular and limited items separately
            c.execute('''SELECT item_id, name, price, description, perk_type, perk_value, limited, available_until 
                        FROM shop ORDER BY limited DESC, price ASC''')
            all_items = c.fetchall()
            
            # Get next rotation time
            c.execute('SELECT available_until FROM shop WHERE limited = TRUE LIMIT 1')
            next_rotation = c.fetchone()

        # Create paginated embeds
        items_per_page = 5
        pages = []
        
        for i in range(0, len(all_items), items_per_page):
            embed = discord.Embed(
                title="🛍️ Luna Shop",
                description="React with ⬅️ ➡️ to navigate pages",
                color=discord.Color.purple()
            )
            
            page_items = all_items[i:i + items_per_page]
            for item_id, name, price, desc, perk_type, perk_value, limited, expiry in page_items:
                rarity = "🌟 LIMITED!" if limited else "📌 Regular"
                bonus = self.format_perk_display(perk_type, perk_value)
                embed.add_field(
                    name=f"{rarity} | {name}",
                    value=f"💰 Price: **{price:,}** {self.currency_name}\n"
                        f"📜 {desc}\n"
                        f"✨ Bonus: {bonus}\n"
                        f"🏷️ ID: {item_id}",
                    inline=False
                )

            if next_rotation:
                expiry_time = datetime.fromisoformat(next_rotation[0])
                time_left = expiry_time - datetime.now()
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                time_text = f"Limited items refresh in: {hours}h {minutes}m | Page {i//items_per_page + 1}/{(len(all_items)-1)//items_per_page + 1}"
                embed.set_footer(text=time_text)
            else:
                embed.set_footer(text=f"Page {i//items_per_page + 1}/{(len(all_items)-1)//items_per_page + 1}")
            pages.append(embed)

        if pages:
            message = await ctx.send(embed=pages[0])
            if len(pages) > 1:
                await message.add_reaction("⬅️")
                await message.add_reaction("➡️")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"]

                current_page = 0
                while True:
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                        if str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
                            current_page += 1
                            await message.edit(embed=pages[current_page])
                        elif str(reaction.emoji) == "⬅️" and current_page > 0:
                            current_page -= 1
                            await message.edit(embed=pages[current_page])

                        await message.remove_reaction(reaction, user)
                    except asyncio.TimeoutError:
                        break
                    
    @commands.hybrid_command(name="buy", description="Buy an item from the shop")
    async def buy(self, ctx: commands.Context, item_id: int, quantity: int = 1):
        user_id = str(ctx.author.id)
        if quantity < 1:
            await ctx.send("Quantity must be positive!")
            return

        # Send initial processing message
        processing_msg = await ctx.send("🔄 Processing your purchase...")

        try:
            with self.db_transaction() as c:
                # Check item exists
                c.execute('SELECT name, price, limited FROM shop WHERE item_id = ?', (item_id,))
                item = c.fetchone()
                
                if not item:
                    await processing_msg.edit(content="Invalid item ID!")
                    return

                name, price, is_limited = item
                
                if is_limited and quantity > 1:
                    await processing_msg.edit(content="Limited items can only be purchased one at a time!")
                    return

                total_cost = price * quantity
                
                if self.get_balance(user_id) < total_cost:
                    await processing_msg.edit(content="You don't have enough Luna!")
                    return

                # Update all shopping metrics
                c.execute('''UPDATE users 
                            SET balance = balance - ?,
                                items_bought = COALESCE(items_bought, 0) + ?,
                                limited_items_bought = CASE WHEN ? THEN COALESCE(limited_items_bought, 0) + 1 ELSE limited_items_bought END,
                                total_spent = COALESCE(total_spent, 0) + ?
                            WHERE user_id = ?''', 
                        (total_cost, quantity, is_limited, total_cost, user_id))
                
                c.execute('''INSERT INTO inventory (user_id, item_id, quantity)
                            VALUES (?, ?, ?)
                            ON CONFLICT(user_id, item_id) 
                            DO UPDATE SET quantity = quantity + ?''',
                        (user_id, item_id, quantity, quantity))

                # Get updated stats for achievement checking
                c.execute('''SELECT items_bought, limited_items_bought, total_spent,
                            (SELECT COUNT(DISTINCT item_id) FROM inventory WHERE user_id = ?) as unique_items
                            FROM users WHERE user_id = ?''', (user_id, user_id))
                items_bought, limited_bought, total_spent, unique_items = c.fetchone()

            # Create success embed
            embed = discord.Embed(
                title="🛍️ Purchase Successful",
                description=f"You bought {quantity}x {name} for **{total_cost:,}** {self.currency_name}!",
                color=discord.Color.green()
            )

            await processing_msg.edit(content=None, embed=embed)

            # Process achievements separately after confirming purchase
            await asyncio.sleep(0.1)  # Small delay to prevent DB lock
            await self.process_purchase_achievements(ctx, user_id, embed)

        except Exception as e:
            await processing_msg.edit(content="❌ An error occurred during purchase. Please try again.")
            raise e

    async def process_purchase_achievements(self, ctx, user_id: str, embed: discord.Embed):
        with self.db_transaction() as c:
            c.execute('SELECT items_bought FROM users WHERE user_id = ?', (user_id,))
            total_bought = c.fetchone()[0]
            
            c.execute('SELECT COUNT(DISTINCT item_id) FROM inventory WHERE user_id = ?', (user_id,))
            unique_items = c.fetchone()[0]

        shop_rewards = self.check_achievement_progress(user_id, "items from shop", total_bought)
        collection_rewards = self.check_achievement_progress(user_id, "each shop item", unique_items)

        if shop_rewards + collection_rewards > 0:
            embed.add_field(
                name="🏆 Achievement Unlocked!",
                value=f"You earned {shop_rewards + collection_rewards:,} {self.currency_name} from achievements!"
            )
            await ctx.send(embed=embed)


    @commands.hybrid_command(name="inventory", description="View your inventory")
    async def inventory(self, ctx: commands.Context):
        with self.db_transaction() as c:
            c.execute('''SELECT s.name, i.quantity, s.description
                        FROM inventory i
                        JOIN shop s ON i.item_id = s.item_id
                        WHERE i.user_id = ?''', (str(ctx.author.id),))
            items = c.fetchall()

        if not items:
            await ctx.send("Your inventory is empty!")
            return

        embed = self.create_transaction_embed("🎒 Your Inventory", "", discord.Color.blue())
        for name, quantity, description in items:
            title, desc = self.format_item_field(name, quantity=quantity, description=description)
            embed.add_field(name=title, value=desc, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="gamble", description="Bet your Luna on a coinflip!")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def gamble(self, ctx: commands.Context, amount: Optional[int] = None):
        if amount is None:
            no_amount_responses = [
                "🌚 Betting moonlight won't work here!",
                "✨ Stardust isn't a valid currency, specify Luna amount!",
                "🎲 The cosmic dice need actual Luna to roll!",
                "💫 Can't gamble with wishes, try some Luna instead!",
                "🌙 The moon says: 'Show me the Luna!'",
                "🎮 You need to place a bet with Luna to play!",
                "🌠 Shooting stars aren't accepted, use Luna!",
                "🎯 Missing something? Like... an amount to bet?",
                "🌌 The galaxy doesn't accept IOUs, specify Luna!",
                "🎪 The lunar casino needs numbers, not dreams!"
            ]
            await ctx.send(random.choice(no_amount_responses))
            return
            
        if amount <= 0:
            await ctx.send("You need to bet a positive amount!")
            return
        
        if not await self.check_funds(ctx, amount):
            return

        message = await ctx.send("🎲 Flipping the lunar coin...")
        await asyncio.sleep(2)

        user_id = str(ctx.author.id)
        
        # Calculate gamble bonus and adjust win chance
        gamble_bonus = self.calculate_user_bonus(user_id, "gamble_bonus")
        win_chance = 0.5 + (gamble_bonus / 2)  # Base 50% + bonus
        won = random.random() < win_chance

        with self.db_transaction() as c:
            c.execute('''UPDATE users SET total_gambles = COALESCE(total_gambles, 0) + 1,
                    gamble_wins = CASE WHEN ? THEN COALESCE(gamble_wins, 0) + 1 ELSE COALESCE(gamble_wins, 0) END
                    WHERE user_id = ?''', (won, user_id))
            c.execute('SELECT gamble_wins FROM users WHERE user_id = ?', (user_id,))
            total_wins = c.fetchone()[0] or 0

        if won:
            winnings = amount * 2  # Double the bet amount
            self.update_balance(user_id, winnings)
            embed = self.create_transaction_embed(
                "🌕 You Won!",
                f"The lunar coin landed in your favor!\nYou won **{winnings:,}** {self.currency_name}!\n"
                f"Luck Bonus: +{int(gamble_bonus * 100)}%",
                discord.Color.green()
            )
        
            rewards = self.check_achievement_progress(user_id, "gambles", total_wins)
            if rewards > 0:
                embed.add_field(
                    name="🏆 Achievement Unlocked!", 
                    value=f"You earned {rewards:,} {self.currency_name} from achievements!"
                )
        else:
            self.update_balance(user_id, -amount)
            embed = self.create_transaction_embed(
                "🌑 You Lost!",
                f"The lunar coin wasn't on your side.\nYou lost **{amount:,}** {self.currency_name}!",
                discord.Color.red()
            )

        await message.edit(content=None, embed=embed)

        
    @commands.hybrid_command(name="trade", description="Trade Luna with another user")
    async def trade(self, ctx: commands.Context, user: discord.Member, amount: int):
        if user.bot or user == ctx.author:
            await ctx.send("You can't trade with yourself or bots!")
            return

        if amount <= 0:
            await ctx.send("Trade amount must be positive!")
            return

        if not await self.check_funds(ctx, amount):
            return

        embed = self.create_transaction_embed(
            "🤝 Trade Offer",
            f"{ctx.author.mention} wants to send you **{amount:,}** {self.currency_name}",
            discord.Color.blue()
        )
        embed.set_footer(text="React ✅ to accept or ❌ to decline")

        trade_msg = await ctx.send(f"{user.mention}", embed=embed)
        await trade_msg.add_reaction("✅")
        await trade_msg.add_reaction("❌")

        def check(reaction, reactor):
            return reactor == user and str(reaction.emoji) in ["✅", "❌"] and reaction.message == trade_msg

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            if str(reaction.emoji) == "✅":
                user_id = str(ctx.author.id)
                target_id = str(user.id)
                
                with self.db_transaction() as c:
                    # Update sender's balance and trade count
                    c.execute('''UPDATE users 
                                SET balance = balance - ?,
                                    trades_completed = COALESCE(trades_completed, 0) + 1 
                                WHERE user_id = ?''', (amount, user_id))
                    
                    # Update receiver's balance
                    c.execute('''INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)''', (target_id,))
                    c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, target_id))
                    
                    # Get updated trade count
                    c.execute('SELECT trades_completed FROM users WHERE user_id = ?', (user_id,))
                    total_trades = c.fetchone()[0]

                rewards = self.check_achievement_progress(user_id, "trades", total_trades)
                success_message = f"🌟 Trade complete! {amount:,} {self.currency_name} transferred."
                if rewards > 0:
                    success_message += f"\n🏆 Achievement Unlocked! You earned {rewards:,} {self.currency_name}!"

                await ctx.send(success_message)
            else:
                await ctx.send("❌ Trade declined!")
        except asyncio.TimeoutError:
            await ctx.send("⏰ Trade offer expired!")

    @commands.hybrid_command(name="debugdb", description="Update database structure")
    @commands.is_owner()
    async def debugdb(self, ctx: Context):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            # Clear existing shop items
            c.execute('DELETE FROM shop')
            
            # Reset version to trigger full reinitialization
            c.execute('DROP TABLE IF EXISTS db_version')
            c.execute('''CREATE TABLE IF NOT EXISTS db_version 
                        (version INTEGER PRIMARY KEY, 
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            c.execute('INSERT INTO db_version (version, updated_at) VALUES (0, CURRENT_TIMESTAMP)')
            
            conn.commit()
            
        # Run setup and initialization
        self.setup_database()
        self.initialize_shop()
        await self.rotate_shop_items()
        
        embed = discord.Embed(
            title="🔧 Database Update",
            description="Database structure has been refreshed and shop items repopulated!",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)


    @commands.hybrid_command(name="debugshop", description="Force shop rotation")
    @commands.is_owner()
    async def debugshop(self, ctx: Context):
        await self.rotate_shop_items()
        embed = discord.Embed(
            title="🔄 Shop Rotation",
            description="Limited items have been refreshed!",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="Cooldown Active",
                description=f"Try again in {error.retry_after:.1f} seconds!",
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Lunacy(bot))

