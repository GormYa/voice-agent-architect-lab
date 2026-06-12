from __future__ import annotations

from datetime import datetime
import json
import sqlite3


DB_PATH = "leads.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT UNIQUE,
                variables TEXT,
                qualified INTEGER DEFAULT 0,
                created TEXT
            )
            """
        )
        conn.commit()


def upsert_lead(call_id: str, variables: dict, qualified: bool = False) -> None:
    variables_json = json.dumps(variables)
    created = datetime.utcnow().isoformat()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO leads (call_id, variables, qualified, created)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(call_id) DO UPDATE SET
                variables = excluded.variables,
                qualified = excluded.qualified,
                created = excluded.created
            """,
            (call_id, variables_json, int(qualified), created),
        )
        conn.commit()


init_db()
