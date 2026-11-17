"""SQLite storage for users, sessions and expenses."""

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    amount_cents INTEGER NOT NULL,
    note TEXT DEFAULT ''
);
"""


def connect(path: str = "ledgerly.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def add_expense(conn, user_id: int, amount_cents: int, note: str) -> int:
    cur = conn.execute(
        "INSERT INTO expenses (user_id, amount_cents, note) VALUES (?, ?, ?)",
        (user_id, amount_cents, note),
    )
    conn.commit()
    return cur.lastrowid


def list_expenses(conn, user_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT id, amount_cents, note FROM expenses WHERE user_id = ? ORDER BY id",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def search_expenses(conn, user_id: int, text: str) -> list[dict]:
    query = (
        "SELECT id, amount_cents, note FROM expenses "
        f"WHERE user_id = {user_id} AND note LIKE '%" + text + "%' ORDER BY id"
    )
    return [dict(r) for r in conn.execute(query).fetchall()]
