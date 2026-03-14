from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = (Path(__file__).resolve().parents[1] / "database" / "ngo.db").resolve()


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS donors (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              email TEXT,
              phone TEXT,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_donors_email_unique ON donors(email);

            CREATE TABLE IF NOT EXISTS donations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              donor_id INTEGER NOT NULL,
              amount REAL NOT NULL CHECK(amount >= 0),
              donation_type TEXT NOT NULL CHECK(donation_type IN ('general','education','medical','food','other')),
              date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              notes TEXT,
              FOREIGN KEY(donor_id) REFERENCES donors(id) ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_donations_donor_id ON donations(donor_id);
            CREATE INDEX IF NOT EXISTS idx_donations_date ON donations(date);

            CREATE TABLE IF NOT EXISTS projects (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              description TEXT,
              allocated_budget REAL NOT NULL CHECK(allocated_budget >= 0),
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS expenses (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              project_id INTEGER NOT NULL,
              amount REAL NOT NULL CHECK(amount >= 0),
              description TEXT NOT NULL,
              date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_expenses_project_id ON expenses(project_id);
            CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);
            """
        )

