"""Aura Database Module — Move History Tracking

SQLite database for recording file move operations.
Supports undo by storing original and new paths with timestamps.
"""

import sqlite3
import os
from datetime import datetime
from loguru import logger

from config import get_config

_config = get_config()
DB_FILE = _config.history_db_file


def _get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the file_moves table if it doesn't exist."""
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_moves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_path TEXT NOT NULL,
                new_path TEXT NOT NULL,
                category TEXT DEFAULT 'Unknown',
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
        logger.debug("Database initialized (file_moves table ready)")
    except Exception as e:
        logger.error(f"Database init error: {e}")
    finally:
        conn.close()


def log_move(original_path: str, new_path: str, category: str = "Unknown") -> None:
    """Record a file move in the history database.
    
    Args:
        original_path: Where the file was before
        new_path: Where the file was moved to
        category: LLM-assigned category
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO file_moves (original_path, new_path, category, timestamp) VALUES (?, ?, ?, ?)",
            (original_path, new_path, category, datetime.now().isoformat()),
        )
        conn.commit()
        logger.info(f"Logged move: {original_path} → {new_path} [{category}]")
    except Exception as e:
        logger.error(f"Error logging move: {e}")
    finally:
        conn.close()


def get_last_move() -> dict | None:
    """Get the most recent file move record.
    
    Returns:
        Dict with id, original_path, new_path, category, timestamp — or None
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM file_moves ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except Exception as e:
        logger.error(f"Error getting last move: {e}")
        return None
    finally:
        conn.close()


def get_recent_moves(n: int = 10) -> list[dict]:
    """Get the N most recent file moves.
    
    Args:
        n: Number of records to return
        
    Returns:
        List of move records (most recent first)
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM file_moves ORDER BY id DESC LIMIT ?", (n,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting recent moves: {e}")
        return []
    finally:
        conn.close()


def delete_move_record(move_id: int) -> bool:
    """Delete a move record by ID (after successful undo).
    
    Args:
        move_id: The database record ID
        
    Returns:
        True if deleted
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM file_moves WHERE id = ?", (move_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting record: {e}")
        return False
    finally:
        conn.close()


def get_move_count() -> int:
    """Get total number of recorded moves."""
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM file_moves")
        return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"Error counting moves: {e}")
        return 0
    finally:
        conn.close()
