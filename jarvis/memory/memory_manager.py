"""
Memory Module
SQLite-based conversation and preference storage.
"""

import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import aiosqlite

from config.settings import Config


class MemoryManager:
    """
    Async SQLite-based memory manager for Jarvis.
    Stores conversations, preferences, and user data.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self._db: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize database and create tables."""
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            self._db = db
            
            # Create conversations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            # Create preferences table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create commands table for command history
            await db.execute("""
                CREATE TABLE IF NOT EXISTS commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    command TEXT NOT NULL,
                    result TEXT,
                    success BOOLEAN
                )
            """)
            
            # Create index for faster queries
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_timestamp 
                ON conversations(timestamp)
            """)
            
            await db.commit()
        
        print(f"[MEMORY] Database initialized at {self.db_path}")
    
    async def save_message(self, role: str, content: str, 
                          metadata: Optional[Dict] = None) -> int:
        """
        Save a conversation message.
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata dict
            
        Returns:
            Message ID
        """
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """INSERT INTO conversations (role, content, metadata) 
                       VALUES (?, ?, ?)""",
                    (role, content, json.dumps(metadata) if metadata else None)
                )
                await db.commit()
                return cursor.lastrowid
    
    async def get_recent_messages(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent conversation messages.
        
        Args:
            limit: Number of messages to retrieve
            
        Returns:
            List of message dicts
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT id, timestamp, role, content, metadata 
                   FROM conversations 
                   ORDER BY timestamp DESC 
                   LIMIT ?""",
                (limit,)
            )
            rows = await cursor.fetchall()
            
            messages = []
            for row in rows:
                msg = {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "role": row["role"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None
                }
                messages.append(msg)
            
            return list(reversed(messages))
    
    async def clear_conversation(self) -> None:
        """Clear all conversation history."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM conversations")
            await db.commit()
        print("[MEMORY] Conversation history cleared")
    
    async def set_preference(self, key: str, value: Any) -> None:
        """
        Set a user preference.
        
        Args:
            key: Preference key
            value: Preference value (will be JSON encoded)
        """
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """INSERT OR REPLACE INTO preferences (key, value, updated_at) 
                       VALUES (?, ?, CURRENT_TIMESTAMP)""",
                    (key, json.dumps(value))
                )
                await db.commit()
    
    async def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get a user preference.
        
        Args:
            key: Preference key
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT value FROM preferences WHERE key = ?",
                (key,)
            )
            row = await cursor.fetchone()
            
            if row:
                return json.loads(row["value"])
            return default
    
    async def get_all_preferences(self) -> Dict[str, Any]:
        """Get all user preferences."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT key, value FROM preferences")
            rows = await cursor.fetchall()
            
            return {row["key"]: json.loads(row["value"]) for row in rows}
    
    async def log_command(self, command: str, result: str = "", 
                         success: bool = True) -> None:
        """
        Log a command execution.
        
        Args:
            command: Command that was executed
            result: Command result
            success: Whether command succeeded
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO commands (command, result, success) 
                   VALUES (?, ?, ?)""",
                (command, result, success)
            )
            await db.commit()
    
    async def get_command_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent command history."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT id, timestamp, command, result, success 
                   FROM commands 
                   ORDER BY timestamp DESC 
                   LIMIT ?""",
                (limit,)
            )
            rows = await cursor.fetchall()
            
            return [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "command": row["command"],
                    "result": row["result"],
                    "success": bool(row["success"])
                }
                for row in rows
            ]
    
    async def search_conversations(self, query: str, 
                                   limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search conversations for a query.
        
        Args:
            query: Search query
            limit: Max results
            
        Returns:
            Matching messages
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT id, timestamp, role, content, metadata 
                   FROM conversations 
                   WHERE content LIKE ? 
                   ORDER BY timestamp DESC 
                   LIMIT ?""",
                (f"%{query}%", limit)
            )
            rows = await cursor.fetchall()
            
            return [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "role": row["role"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None
                }
                for row in rows
            ]
    
    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None
