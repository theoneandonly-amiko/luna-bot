import aiosqlite
import shutil
import os
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    pass

class LevelDatabase:
    def __init__(self, db_path: str = 'cogs/data/levelup.db'):
        self.db_path = db_path

    async def backup_db(self) -> str:
        """Create a timestamped backup of the database"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.db_path}.backup_{timestamp}"
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backup created at {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            raise DatabaseError("Backup creation failed")

    async def execute_transaction(self, queries: List[Tuple[str, tuple]]) -> None:
        """Execute multiple queries in a single transaction"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute("BEGIN TRANSACTION")
                for query, params in queries:
                    await db.execute(query, params)
                await db.commit()
            except Exception as e:
                await db.rollback()
                logger.error(f"Transaction failed: {e}")
                raise DatabaseError(f"Database transaction failed: {str(e)}")


    async def get_user_level(self, guild_id: str, user_id: str) -> Dict:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT xp, level FROM levels WHERE guild_id = ? AND user_id = ?',
                (guild_id, user_id)
            ) as cursor:
                result = await cursor.fetchone()
                if result:
                    return {"xp": result[0], "level": result[1]}
                return {"xp": 0, "level": 1}
                
    async def update_user_level(self, guild_id: str, user_id: str, xp: int, level: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO levels (guild_id, user_id, xp, level)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id, user_id) 
                DO UPDATE SET xp = ?, level = ?
            ''', (guild_id, user_id, xp, level, xp, level))
            await db.commit()

    async def get_guild_config(self, guild_id: str) -> Dict:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    'SELECT xp_cooldown, xp_amount, level_channel_id, is_blocked FROM guild_config WHERE guild_id = ?',
                    (guild_id,)
                ) as cursor:
                    result = await cursor.fetchone()
                    if result:
                        return {
                            "xp_cooldown": result[0],
                            "xp_amount": result[1],
                            "level_channel_id": result[2],
                            "is_blocked": bool(result[3])
                        }
                    return {}
        except Exception as e:
            logger.error(f"Failed to get guild config: {e}")
            raise DatabaseError(f"Config retrieval failed: {str(e)}")


    async def add_xp(self, guild_id: str, user_id: str, xp_amount: int) -> tuple[bool, int, int]:
        """Add XP to user and return (leveled_up, new_level, current_xp)"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    'SELECT level, xp FROM levels WHERE guild_id = ? AND user_id = ?',
                    (guild_id, user_id)
                ) as cursor:
                    result = await cursor.fetchone()
                    current_level = result[0] if result else 1
                    current_xp = result[1] if result else 0

                current_xp += xp_amount
                leveled_up = False

                while True:
                    xp_needed = int(100 * (current_level ** 1.5))
                    if current_xp >= xp_needed:
                        current_xp -= xp_needed
                        current_level += 1
                        leveled_up = True
                    else:
                        break

                await db.execute('''
                    INSERT INTO levels (guild_id, user_id, xp, level)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(guild_id, user_id) 
                    DO UPDATE SET xp = ?, level = ?
                ''', (guild_id, user_id, current_xp, current_level, current_xp, current_level))
                await db.commit()

                return leveled_up, current_level, current_xp
        except Exception as e:
            logger.error(f"Failed to add XP: {e}")
            raise DatabaseError(f"XP addition failed: {str(e)}")


    async def migrate_roles(self, guild_id: str, roles_data: dict):
        async with aiosqlite.connect(self.db_path) as db:
            for level, role_id in roles_data.items():
                await db.execute('''
                    INSERT INTO level_roles (guild_id, level, role_id)
                    VALUES (?, ?, ?)
                    ON CONFLICT(guild_id, level) 
                    DO UPDATE SET role_id = ?
                ''', (guild_id, int(level), role_id, role_id))
            await db.commit()

    async def migrate_config(self, guild_id: str, config_data: dict):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO guild_config 
                (guild_id, xp_cooldown, xp_amount, level_channel_id, is_blocked)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                xp_cooldown = ?, xp_amount = ?, level_channel_id = ?, is_blocked = ?
            ''', (
                guild_id,
                config_data.get('xp_cooldown', 10),
                config_data.get('xp_amount', 10),
                config_data.get('level_channel', None),
                guild_id in config_data.get('blocked_guilds', []),
                config_data.get('xp_cooldown', 10),
                config_data.get('xp_amount', 10),
                config_data.get('level_channel', None),
                guild_id in config_data.get('blocked_guilds', [])
            ))
            await db.commit()

    async def get_top_users(self, guild_id: str, limit: int = 10) -> List[tuple]:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    'SELECT user_id, level, xp FROM levels WHERE guild_id = ? ORDER BY level DESC, xp DESC LIMIT ?',
                    (guild_id, limit)
                ) as cursor:
                    return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to get top users: {e}")
            raise DatabaseError(f"Leaderboard retrieval failed: {str(e)}")

    async def reset_user_level(self, guild_id: str, user_id: str):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    'UPDATE levels SET xp = 0, level = 1 WHERE guild_id = ? AND user_id = ?',
                    (guild_id, user_id)
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to reset user level: {e}")
            raise DatabaseError(f"Level reset failed: {str(e)}")


    async def set_level_role(self, guild_id: str, level: int, role_id: int):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO level_roles (guild_id, level, role_id)
                    VALUES (?, ?, ?)
                    ON CONFLICT(guild_id, level) DO UPDATE SET role_id = ?
                ''', (guild_id, level, role_id, role_id))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to set level role: {e}")
            raise DatabaseError(f"Role assignment failed: {str(e)}")

    async def get_level_roles(self, guild_id: str) -> List[tuple]:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    'SELECT level, role_id FROM level_roles WHERE guild_id = ? ORDER BY level',
                    (guild_id,)
                ) as cursor:
                    return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to get level roles: {e}")
            raise DatabaseError(f"Role retrieval failed: {str(e)}")



    async def update_guild_config(self, guild_id: str, **kwargs):
        async with aiosqlite.connect(self.db_path) as db:
            fields = ', '.join(f'{k} = ?' for k in kwargs.keys())
            values = tuple(kwargs.values()) + (guild_id,)
            await db.execute(
                f'UPDATE guild_config SET {fields} WHERE guild_id = ?',
                values
            )
            await db.commit()

    async def update_xp_settings(self, guild_id: str, cooldown: int = None, amount: int = None):
        try:
            queries = []
            if cooldown is not None:
                queries.append((
                    'UPDATE guild_config SET xp_cooldown = ? WHERE guild_id = ?',
                    (cooldown, guild_id)
                ))
            if amount is not None:
                queries.append((
                    'UPDATE guild_config SET xp_amount = ? WHERE guild_id = ?',
                    (amount, guild_id)
                ))
            await self.execute_transaction(queries)
        except Exception as e:
            logger.error(f"Failed to update XP settings: {e}")
            raise DatabaseError(f"XP settings update failed: {str(e)}")

    async def toggle_guild_block(self, guild_id: str) -> bool:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    'SELECT is_blocked FROM guild_config WHERE guild_id = ?',
                    (guild_id,)
                ) as cursor:
                    result = await cursor.fetchone()
                    current_status = bool(result[0]) if result else False
                    
                new_status = not current_status
                await db.execute('''
                    INSERT INTO guild_config (guild_id, is_blocked)
                    VALUES (?, ?)
                    ON CONFLICT(guild_id) DO UPDATE SET is_blocked = ?
                ''', (guild_id, new_status, new_status))
                await db.commit()
                return new_status
        except Exception as e:
            logger.error(f"Failed to toggle guild block: {e}")
            raise DatabaseError(f"Guild block toggle failed: {str(e)}")

    async def set_level_channel(self, guild_id: str, channel_id: int):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO guild_config (guild_id, level_channel_id)
                    VALUES (?, ?)
                    ON CONFLICT(guild_id) DO UPDATE SET level_channel_id = ?
                ''', (guild_id, channel_id, channel_id))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to set level channel: {e}")
            raise DatabaseError(f"Channel setting failed: {str(e)}")


    async def toggle_restricted_entity(self, guild_id: str, entity_id: str, entity_type: str) -> bool:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    'SELECT 1 FROM restricted_entities WHERE guild_id = ? AND entity_id = ? AND entity_type = ?',
                    (guild_id, entity_id, entity_type)
                ) as cursor:
                    exists = await cursor.fetchone()
                    
                if exists:
                    await db.execute(
                        'DELETE FROM restricted_entities WHERE guild_id = ? AND entity_id = ? AND entity_type = ?',
                        (guild_id, entity_id, entity_type)
                    )
                    result = False
                else:
                    await db.execute(
                        'INSERT INTO restricted_entities (guild_id, entity_id, entity_type) VALUES (?, ?, ?)',
                        (guild_id, entity_id, entity_type)
                    )
                    result = True
                    
                await db.commit()
                return result
        except Exception as e:
            logger.error(f"Failed to toggle restricted entity: {e}")
            raise DatabaseError(f"Entity restriction toggle failed: {str(e)}")

    async def bulk_add_xp(self, guild_id: str, user_xp_mapping: dict) -> List[tuple]:
        """
        Bulk add XP to multiple users and return list of (user_id, leveled_up, new_level)
        """
        try:
            results = []
            async with aiosqlite.connect(self.db_path) as db:
                for user_id, xp_amount in user_xp_mapping.items():
                    # Get current level and XP
                    async with db.execute(
                        'SELECT level, xp FROM levels WHERE guild_id = ? AND user_id = ?',
                        (guild_id, user_id)
                    ) as cursor:
                        result = await cursor.fetchone()
                        current_level = result[0] if result else 1
                        current_xp = result[1] if result else 0

                    # Calculate new level and XP
                    new_xp = current_xp + xp_amount
                    leveled_up = False
                    
                    while True:
                        xp_needed = int(100 * (current_level ** 1.5))
                        if new_xp >= xp_needed:
                            new_xp -= xp_needed
                            current_level += 1
                            leveled_up = True
                        else:
                            break

                    # Update database
                    await db.execute('''
                        INSERT INTO levels (guild_id, user_id, xp, level)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(guild_id, user_id) 
                        DO UPDATE SET xp = ?, level = ?
                    ''', (guild_id, user_id, new_xp, current_level, new_xp, current_level))
                    
                    results.append((user_id, leveled_up, current_level))
                
                await db.commit()
                return results
        except Exception as e:
            logger.error(f"Failed to bulk add XP: {e}")
            raise DatabaseError(f"Bulk XP addition failed: {str(e)}")

    async def set_xp_multiplier(self, guild_id: str, multiplier_type: str, target_id: str, multiplier: float, duration_hours: int = None):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                expires_at = None
                if duration_hours:
                    expires_at = datetime.now() + timedelta(hours=duration_hours)
                
                await db.execute('''
                    INSERT INTO xp_multipliers (guild_id, multiplier_type, target_id, multiplier, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(guild_id, multiplier_type, target_id) 
                    DO UPDATE SET multiplier = ?, expires_at = ?
                ''', (guild_id, multiplier_type, target_id, multiplier, expires_at, multiplier, expires_at))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to set XP multiplier: {e}")
            raise DatabaseError(f"XP multiplier setting failed: {str(e)}")

    async def get_active_multipliers(self, guild_id: str) -> List[tuple]:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                current_time = datetime.now()
                async with db.execute('''
                    SELECT multiplier_type, target_id, multiplier, expires_at 
                    FROM xp_multipliers 
                    WHERE guild_id = ? AND (expires_at IS NULL OR expires_at > ?)
                ''', (guild_id, current_time)) as cursor:
                    return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to get active multipliers: {e}")
            raise DatabaseError(f"Multiplier retrieval failed: {str(e)}")

    async def create_xp_event(self, guild_id: str, event_name: str, multiplier: float, duration_hours: int, roles: List[int] = None):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                end_time = datetime.now() + timedelta(hours=duration_hours)
                
                # Create event multiplier
                await db.execute('''
                    INSERT INTO xp_multipliers (guild_id, multiplier_type, target_id, multiplier, expires_at)
                    VALUES (?, 'event', ?, ?, ?)
                ''', (guild_id, event_name, multiplier, end_time))
                
                # If specific roles are targeted, create role multipliers
                if roles:
                    for role_id in roles:
                        await db.execute('''
                            INSERT INTO xp_multipliers (guild_id, multiplier_type, target_id, multiplier, expires_at)
                            VALUES (?, 'role', ?, ?, ?)
                        ''', (guild_id, str(role_id), multiplier, end_time))
                
                await db.commit()
                return end_time
        except Exception as e:
            logger.error(f"Failed to create XP event: {e}")
            raise DatabaseError(f"XP event creation failed: {str(e)}")
