
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from reproducibility import fingerprint_text

DB_PATH = Path(__file__).resolve().parent / "data" / "experiments.db"

BASE_SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt TEXT NOT NULL,
    ticket_count INTEGER NOT NULL,
    category_accuracy REAL NOT NULL,
    order_id_accuracy REAL NOT NULL,
    lookup_accuracy REAL NOT NULL,
    overall_field_accuracy REAL NOT NULL,
    average_latency_ms REAL NOT NULL,
    total_input_tokens INTEGER NOT NULL,
    total_output_tokens INTEGER NOT NULL,
    details_json TEXT NOT NULL DEFAULT '[]'
)
"""

MIGRATIONS = {
    "prompt_name": (
        "ALTER TABLE experiments "
        "ADD COLUMN prompt_name TEXT NOT NULL DEFAULT 'unnamed'"
    ),
    "prompt_version": (
        "ALTER TABLE experiments "
        "ADD COLUMN prompt_version TEXT NOT NULL DEFAULT 'v1'"
    ),
    "prompt_hash": (
        "ALTER TABLE experiments "
        "ADD COLUMN prompt_hash TEXT NOT NULL DEFAULT ''"
    ),
    "manifest_json": (
        "ALTER TABLE experiments "
        "ADD COLUMN manifest_json TEXT NOT NULL DEFAULT '{}'"
    ),
}


def get_connection() -> sqlite3.Connection:
    """Create the database directory and return a SQLite connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    """Create the experiments table and apply missing schema migrations."""
    with get_connection() as connection:
        connection.execute(BASE_SCHEMA)

        existing_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(experiments)"
            ).fetchall()
        }

        for column_name, migration_sql in MIGRATIONS.items():
            if column_name not in existing_columns:
                connection.execute(migration_sql)


def save_experiment(
    prompt: str,
    result: dict[str, Any],
    prompt_name: str = "unnamed",
    prompt_version: str = "v1",
    manifest: dict[str, Any] | None = None,
) -> int:
    """
    Save an evaluation result and return its database ID.

    `result` is the dictionary returned by run_prompt_evaluation().
    `manifest` is the reproducibility metadata built for this experiment.
    """
    initialize_database()

    summary = result["summary"]
    manifest_data = manifest or {}
    details = result.get("details", [])

    prompt_hash = fingerprint_text(prompt)

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO experiments (
                created_at,
                model,
                prompt,
                ticket_count,
                category_accuracy,
                order_id_accuracy,
                lookup_accuracy,
                overall_field_accuracy,
                average_latency_ms,
                total_input_tokens,
                total_output_tokens,
                details_json,
                prompt_name,
                prompt_version,
                prompt_hash,
                manifest_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(UTC).isoformat(),
                result["model"],
                prompt,
                result["ticket_count"],
                summary["category_accuracy"],
                summary["order_id_accuracy"],
                summary["lookup_accuracy"],
                summary["overall_field_accuracy"],
                result["average_latency_ms"],
                result["total_input_tokens"],
                result["total_output_tokens"],
                json.dumps(details, sort_keys=True),
                prompt_name,
                prompt_version,
                prompt_hash,
                json.dumps(manifest_data, sort_keys=True),
            ),
        )

        return int(cursor.lastrowid)


def list_experiments(limit: int = 50) -> list[dict[str, Any]]:
    """Return recent experiment summaries, newest first."""
    initialize_database()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                created_at,
                model,
                prompt_name,
                prompt_version,
                prompt_hash,
                ticket_count,
                category_accuracy,
                order_id_accuracy,
                lookup_accuracy,
                overall_field_accuracy,
                average_latency_ms,
                total_input_tokens,
                total_output_tokens
            FROM experiments
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(1, limit),),
        ).fetchall()

    return [dict(row) for row in rows]


def get_experiment(experiment_id: int) -> dict[str, Any] | None:
    """Return one experiment, including parsed details and manifest."""
    initialize_database()

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM experiments WHERE id = ?",
            (experiment_id,),
        ).fetchone()

    if row is None:
        return None

    experiment = dict(row)
    experiment["details"] = json.loads(
        experiment.pop("details_json", "[]") or "[]"
    )
    experiment["manifest"] = json.loads(
        experiment.pop("manifest_json", "{}") or "{}"
    )

    return experiment

