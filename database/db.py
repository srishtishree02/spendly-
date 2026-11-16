import os
import sqlite3

from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "expense_tracker.db",
)


def get_db():
    """Return a SQLite connection with dict-like rows and foreign keys enabled.

    The caller is responsible for closing the connection.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they do not already exist."""
    conn = get_db()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at    TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                amount      REAL NOT NULL CHECK (amount > 0),  -- INR
                category    TEXT NOT NULL,
                date        TEXT NOT NULL,                     -- YYYY-MM-DD
                description TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_expenses_user_date
                ON expenses (user_id, date);
            """
        )
        conn.commit()
    finally:
        conn.close()


def seed_db():
    """Insert a demo user and sample INR expenses. Does nothing if users exist."""
    conn = get_db()
    try:
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
            return

        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        user_id = cur.lastrowid

        expenses = [
            (450.00, "Food", "2026-11-02", "Lunch with team"),
            (1250.00, "Bills", "2026-11-03", "Electricity bill"),
            (180.00, "Transport", "2026-11-04", "Auto rickshaw to office"),
            (2399.00, "Shopping", "2026-11-06", "Running shoes"),
            (650.00, "Health", "2026-11-08", "Pharmacy"),
            (199.00, "Entertainment", "2026-11-09", "Movie ticket"),
            (899.00, "Food", "2026-11-11", "Weekly groceries"),
            (499.00, "Bills", "2026-11-13", "Mobile recharge"),
        ]
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            [(user_id, *e) for e in expenses],
        )
        conn.commit()
    finally:
        conn.close()
