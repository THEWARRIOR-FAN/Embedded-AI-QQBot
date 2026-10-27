"""
QQ 群聊机器人 - 短期记忆（最近 N 轮对话）+ 简单的长期用户档案。
存储用 SQLite，单文件即可。
"""
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(os.environ.get("DATA_DIR", str(Path(__file__).parent.parent / "data"))) / "memory.db"


def configure(data_dir: Path) -> None:
    """Set the runtime data directory before the first database operation."""
    global DB_PATH
    DB_PATH = Path(data_dir) / "memory.db"
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id TEXT PRIMARY KEY,
            nickname TEXT,
            mood TEXT,
            topics TEXT,
            last_seen DATETIME
        )
    """)
    c.commit()
    return c


def get_history(user_id: str, limit_turns: int = 8) -> list[dict]:
    """拉最近 limit_turns 轮对话（一轮 = user + assistant 两条）。"""
    c = _conn()
    rows = c.execute(
        """
        SELECT role, content FROM (
            SELECT id, role, content FROM messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        ) ORDER BY id ASC
        """,
        (user_id, limit_turns * 2),
    ).fetchall()
    c.close()
    return [{"role": r, "content": cnt} for r, cnt in rows]


def save_turn(user_id: str, user_msg: str, bot_msg: str) -> None:
    c = _conn()
    c.execute("INSERT INTO messages (user_id, role, content) VALUES (?, 'user', ?)", (user_id, user_msg))
    c.execute("INSERT INTO messages (user_id, role, content) VALUES (?, 'assistant', ?)", (user_id, bot_msg))
    # 简单清理：只保留每个用户最近 200 条
    c.execute("""
        DELETE FROM messages WHERE user_id = ? AND id NOT IN (
            SELECT id FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT 200
        )
    """, (user_id, user_id))
    c.commit()
    c.close()


def update_profile(user_id: str, **kwargs) -> None:
    c = _conn()
    existing = c.execute("SELECT * FROM user_profile WHERE user_id=?", (user_id,)).fetchone()
    if existing:
        for k, v in kwargs.items():
            c.execute(f"UPDATE user_profile SET {k}=? WHERE user_id=?", (v, user_id))
        c.execute("UPDATE user_profile SET last_seen=CURRENT_TIMESTAMP WHERE user_id=?", (user_id,))
    else:
        cols = ["user_id"] + list(kwargs.keys()) + ["last_seen"]
        placeholders = ",".join("?" for _ in cols)
        values = [user_id] + list(kwargs.values()) + [datetime.now().isoformat()]
        c.execute(f"INSERT INTO user_profile ({','.join(cols)}) VALUES ({placeholders})", values)
    c.commit()
    c.close()


def get_profile(user_id: str) -> dict:
    c = _conn()
    row = c.execute("SELECT nickname, mood, topics, last_seen FROM user_profile WHERE user_id=?", (user_id,)).fetchone()
    c.close()
    if not row:
        return {}
    return {"nickname": row[0], "mood": row[1], "topics": row[2], "last_seen": row[3]}
