import sqlite3
import json
import os
from datetime import datetime

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "users.db")
_DB_INITIALIZED = False

def _get_conn():
    global _DB_INITIALIZED
    if not _DB_INITIALIZED:
        try:
            init_db()
        except Exception:
            import logging
            logging.getLogger(__name__).warning("lazy init_db failed", exc_info=True)
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

BETA_MAX = 100

def _init_db_conn():
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    global _DB_INITIALIZED
    conn = _init_db_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            beta_slot INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    try:
        conn.execute("ALTER TABLE users ADD COLUMN beta_slot INTEGER")
    except:
        pass
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(username, key)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()
    _DB_INITIALIZED = True

def count_users():
    conn = _get_conn()
    c = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return c

def register_beta_user(username, password=""):
    conn = _get_conn()
    c = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if c >= BETA_MAX:
        conn.close()
        return False, 0
    slot = c + 1
    conn.execute("INSERT OR IGNORE INTO users (username, beta_slot) VALUES (?, ?)", (username, slot))
    if conn.total_changes == 0:
        conn.close()
        return False, slot
    conn.execute("INSERT OR REPLACE INTO sessions (username, key, value) VALUES (?, 'password', ?)", (username, password))
    conn.commit()
    conn.close()
    return True, slot

def verify_user(username, password):
    conn = _get_conn()
    row = conn.execute("SELECT value FROM sessions WHERE username=? AND key='password'", (username,)).fetchone()
    conn.close()
    if row:
        return row[0] == password
    return False

def is_founding_member(username):
    conn = _get_conn()
    row = conn.execute("SELECT beta_slot FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return row and row[0] is not None and 1 <= row[0] <= BETA_MAX

def get_beta_progress():
    conn = _get_conn()
    c = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return c, BETA_MAX

def save_state(username, data):
    conn = _get_conn()
    for k, v in data.items():
        val = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
        conn.execute("""
            INSERT INTO sessions (username, key, value, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(username, key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """, (username, k, val))
    conn.commit()
    conn.close()

def load_state(username):
    conn = _get_conn()
    rows = conn.execute("SELECT key, value FROM sessions WHERE username=?", (username,)).fetchall()
    conn.close()
    data = {}
    for row in rows:
        try:
            data[row["key"]] = json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            data[row["key"]] = row["value"]
    return data

def save_chat(username, role, content):
    conn = _get_conn()
    conn.execute("INSERT INTO chat_history (username, role, content) VALUES (?, ?, ?)", (username, role, content))
    conn.commit()
    conn.close()

def load_chat(username, limit=50):
    conn = _get_conn()
    rows = conn.execute(
        "SELECT role, content, created_at FROM chat_history WHERE username=? ORDER BY id DESC LIMIT ?",
        (username, limit)
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"], "time": r["created_at"]} for r in reversed(rows)]

def ensure_user(username):
    conn = _get_conn()
    conn.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()

try:
    init_db()
except Exception as e:
    import logging
    logging.getLogger(__name__).warning("init_db failed: %s", e)
