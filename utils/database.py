import aiosqlite
import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path: str = "data/bot_database.db"):
        self.db_path = db_path
        # Ensure data directory exists
        Path(db_path).parent.mkdir(exist_ok=True)
        
    async def init_database(self):
        """Initialize the database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    display_name TEXT,
                    join_date TEXT,
                    last_seen TEXT,
                    message_count INTEGER DEFAULT 0,
                    settings TEXT DEFAULT '{}'
                )
            """)
            
            # Events table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    creator_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    event_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    max_participants INTEGER DEFAULT -1,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # Event participants table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS event_participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    joined_at TEXT NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES events (id),
                    UNIQUE(event_id, user_id)
                )
            """)
            
            # Reminders table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    remind_time TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_recurring BOOLEAN DEFAULT FALSE,
                    recurring_pattern TEXT,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # Media shares table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS media_shares (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    media_type TEXT NOT NULL,
                    media_url TEXT NOT NULL,
                    description TEXT,
                    shared_at TEXT NOT NULL
                )
            """)
            
            # Bot logs table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    module TEXT,
                    user_id INTEGER,
                    guild_id INTEGER,
                    timestamp TEXT NOT NULL
                )
            """)
            
            await db.commit()
    
    # User management methods
    async def add_or_update_user(self, user_id: int, username: str, display_name: str = None):
        """Add or update user information"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO users (user_id, username, display_name, join_date, last_seen)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, display_name, datetime.now().isoformat(), datetime.now().isoformat()))
            await db.commit()
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def update_user_activity(self, user_id: int):
        """Update user's last seen time and increment message count"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users 
                SET last_seen = ?, message_count = message_count + 1 
                WHERE user_id = ?
            """, (datetime.now().isoformat(), user_id))
            await db.commit()
    
    # Event management methods
    async def create_event(self, title: str, description: str, creator_id: int, 
                          guild_id: int, channel_id: int, event_date: str, 
                          max_participants: int = -1) -> int:
        """Create a new event and return its ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO events (title, description, creator_id, guild_id, channel_id, 
                                  event_date, created_at, max_participants)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, description, creator_id, guild_id, channel_id, 
                  event_date, datetime.now().isoformat(), max_participants))
            await db.commit()
            return cursor.lastrowid
    
    async def get_event(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Get event information"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM events WHERE id = ?", (event_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def get_guild_events(self, guild_id: int, status: str = 'active') -> List[Dict[str, Any]]:
        """Get all events for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM events WHERE guild_id = ? AND status = ? 
                ORDER BY event_date ASC
            """, (guild_id, status)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def join_event(self, event_id: int, user_id: int) -> bool:
        """Add user to event participants"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO event_participants (event_id, user_id, joined_at)
                    VALUES (?, ?, ?)
                """, (event_id, user_id, datetime.now().isoformat()))
                await db.commit()
                return True
        except aiosqlite.IntegrityError:
            return False  # User already joined
    
    async def leave_event(self, event_id: int, user_id: int) -> bool:
        """Remove user from event participants"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                DELETE FROM event_participants WHERE event_id = ? AND user_id = ?
            """, (event_id, user_id))
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_event_participants(self, event_id: int) -> List[int]:
        """Get list of user IDs participating in an event"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id FROM event_participants WHERE event_id = ?
            """, (event_id,)) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
    
    # Reminder management methods
    async def create_reminder(self, user_id: int, guild_id: int, channel_id: int,
                            message: str, remind_time: str, is_recurring: bool = False,
                            recurring_pattern: str = None) -> int:
        """Create a new reminder"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO reminders (user_id, guild_id, channel_id, message, remind_time,
                                     created_at, is_recurring, recurring_pattern)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, guild_id, channel_id, message, remind_time,
                  datetime.now().isoformat(), is_recurring, recurring_pattern))
            await db.commit()
            return cursor.lastrowid
    
    async def get_active_reminders(self) -> List[Dict[str, Any]]:
        """Get all active reminders"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM reminders WHERE status = 'active'
                ORDER BY remind_time ASC
            """) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_user_reminders(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all reminders for a specific user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM reminders WHERE user_id = ? AND status = 'active'
                ORDER BY remind_time ASC
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def complete_reminder(self, reminder_id: int):
        """Mark a reminder as completed"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE reminders SET status = 'completed' WHERE id = ?
            """, (reminder_id,))
            await db.commit()
    
    async def delete_reminder(self, reminder_id: int, user_id: int) -> bool:
        """Delete a reminder (only by its creator)"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                DELETE FROM reminders WHERE id = ? AND user_id = ?
            """, (reminder_id, user_id))
            await db.commit()
            return cursor.rowcount > 0
    
    # Media sharing methods
    async def log_media_share(self, user_id: int, guild_id: int, channel_id: int,
                            media_type: str, media_url: str, description: str = None):
        """Log a media share"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO media_shares (user_id, guild_id, channel_id, media_type,
                                        media_url, description, shared_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, guild_id, channel_id, media_type, media_url, 
                  description, datetime.now().isoformat()))
            await db.commit()
    
    # Logging methods
    async def log_event(self, level: str, message: str, module: str = None,
                       user_id: int = None, guild_id: int = None):
        """Log a bot event"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO bot_logs (level, message, module, user_id, guild_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (level, message, module, user_id, guild_id, datetime.now().isoformat()))
            await db.commit()
    
    async def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent bot logs"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM bot_logs ORDER BY timestamp DESC LIMIT ?
            """, (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

# Global database instance
db_manager = DatabaseManager()
