from __future__ import annotations

from datetime import datetime
import json
import sqlite3


DB_PATH = "leads.db"


def store_lead(call_id: str, variables: dict) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                call_id TEXT,
                variables TEXT,
                created TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO leads (call_id, variables, created) VALUES (?, ?, ?)",
            (call_id, json.dumps(variables), datetime.utcnow().isoformat()),
        )
        conn.commit()
