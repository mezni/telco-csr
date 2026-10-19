import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "data" / "audit.db"


def get_connection() -> sqlite3.Connection:
    """Open the audit database and ensure its directory exists."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_audit_database() -> None:
    """Create the audit table if it does not exist."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                ticket_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                details_json TEXT NOT NULL DEFAULT '{}'
            )
            """
        )


def log_event(
    ticket_id: str,
    event_type: str,
    details: dict[str, Any] | None = None,
) -> int:
    """Persist an audit event and return its database ID."""
    if not isinstance(ticket_id, str) or not ticket_id.strip():
        raise ValueError("ticket_id must be a non-empty string.")

    if not isinstance(event_type, str) or not event_type.strip():
        raise ValueError("event_type must be a non-empty string.")

    event_details = details or {}

    if not isinstance(event_details, dict):
        raise ValueError("details must be a dictionary.")

    # Validate that details can be serialized before writing.
    details_json = json.dumps(event_details, sort_keys=True)

    initialize_audit_database()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO audit_events (
                timestamp,
                ticket_id,
                event_type,
                details_json
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                datetime.now(UTC).isoformat(),
                ticket_id.strip(),
                event_type.strip(),
                details_json,
            ),
        )
        return int(cursor.lastrowid)


def list_events(
    ticket_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Return recent audit events, optionally for one ticket."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer.")

    initialize_audit_database()

    with get_connection() as connection:
        if ticket_id is None:
            rows = connection.execute(
                """
                SELECT * FROM audit_events
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT * FROM audit_events
                WHERE ticket_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (ticket_id, limit),
            ).fetchall()

    events = []
    for row in rows:
        event = dict(row)
        event["details"] = json.loads(event.pop("details_json"))
        events.append(event)

    return events
