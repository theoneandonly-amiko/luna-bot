import sqlite3
import aiosqlite

async def init_db():
    async with aiosqlite.connect('cogs/data/levelup.db') as db:
        # Create version tracking table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS db_version (
                version INTEGER PRIMARY KEY,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create levels table with indexes
        await db.execute('''
            CREATE TABLE IF NOT EXISTS levels (
                guild_id TEXT,
                user_id TEXT,
                xp INTEGER DEFAULT 0 CHECK (xp >= 0),
                level INTEGER DEFAULT 1 CHECK (level >= 1),
                last_xp_gain TIMESTAMP,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_levels_guild ON levels(guild_id)')
        
        # Create level roles table with foreign key
        await db.execute('''
            CREATE TABLE IF NOT EXISTS level_roles (
                guild_id TEXT,
                level INTEGER CHECK (level >= 1),
                role_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, level)
            )
        ''')
        
        # Create guild config table with constraints
        await db.execute('''
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id TEXT PRIMARY KEY,
                xp_cooldown INTEGER DEFAULT 10 CHECK (xp_cooldown >= 1),
                xp_amount INTEGER DEFAULT 10 CHECK (xp_amount >= 0),
                level_channel_id INTEGER,
                is_blocked BOOLEAN DEFAULT 0
            )
        ''')
        
        # Create restricted entities table with type constraint
        await db.execute('''
            CREATE TABLE IF NOT EXISTS restricted_entities (
                guild_id TEXT,
                entity_id TEXT,
                entity_type TEXT CHECK (entity_type IN ('user', 'channel')),
                PRIMARY KEY (guild_id, entity_id, entity_type)
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS xp_multipliers (
                guild_id TEXT,
                multiplier_type TEXT CHECK (multiplier_type IN ('server', 'role', 'user')),
                target_id TEXT,
                multiplier FLOAT DEFAULT 1.0,
                expires_at TIMESTAMP,
                PRIMARY KEY (guild_id, multiplier_type, target_id)
            )
        ''')

        await db.commit()
