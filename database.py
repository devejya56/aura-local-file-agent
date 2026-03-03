import sqlite3
import os
from datetime import datetime

DB_FILE = "aura_history.db"

def init_db():
    """Creates the history table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_path TEXT,
            new_path TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_move(original_path, new_path):
    """Logs a file movement into the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO file_moves (original_path, new_path, timestamp)
        VALUES (?, ?, ?)
    ''', (original_path, new_path, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# Initialize DB on import
init_db()
