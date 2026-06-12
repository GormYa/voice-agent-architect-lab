from __future__ import annotations

from pathlib import Path
import sqlite3


DB_PATH = Path(__file__).resolve().parents[1] / "ep6-retell-custom-backend" / "leads.db"
WIDTHS = [14, 9, 10, 12, 14, 19]
HEADERS = ["call_id", "qualified", "budget", "timeline", "location", "created"]


def fit(value: object, width: int) -> str:
    text = "" if value is None else str(value)
    if len(text) <= width:
        return text
    return text[: width - 3] + "..."


def print_row(values: list[object]) -> None:
    cells = [fit(value, width).ljust(width) for value, width in zip(values, WIDTHS)]
    print(" ".join(cells))


def main() -> None:
    if not DB_PATH.exists():
        print(f"No leads database found at {DB_PATH}")
        return

    query = """
        SELECT
            call_id,
            qualified,
            json_extract(variables, '$.budget') AS budget,
            json_extract(variables, '$.timeline') AS timeline,
            json_extract(variables, '$.location') AS location,
            created
        FROM leads
        ORDER BY created DESC
        LIMIT 10
    """

    try:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(query).fetchall()
    except sqlite3.OperationalError as exc:
        print(f"Could not query leads table: {exc}")
        return

    print_row(HEADERS)
    print_row(["-" * width for width in WIDTHS])
    for row in rows:
        print_row(list(row))


if __name__ == "__main__":
    main()
