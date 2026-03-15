# sqlite connection and tables

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "backpack.db"


def get_db():
    """Yield a new DB connection per request. check_same_thread=False so FastAPI's thread pool can use it."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Create tables at startup. Uses its own connection (get_db is a generator for request scope)."""
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT DEFAULT '',
            folder_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            done INTEGER DEFAULT 0,
            folder_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER   -- which folder this is in, null = top level
        );
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            front TEXT NOT NULL,
            back TEXT NOT NULL,
            folder_id INTEGER
        );
    """)
    # if we already had these tables without new columns, add them
    try:
        conn.execute("ALTER TABLE folders ADD COLUMN parent_id INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE notes ADD COLUMN folder_id INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE todos ADD COLUMN folder_id INTEGER")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE folders ADD COLUMN is_flashcard_set INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    # need to add another one for game
    conn.commit()
    conn.close()