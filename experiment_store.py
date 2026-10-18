import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "experiments.db"

def fingerprint_prompt(prompt: str) -> str:
    """Return a SHA-256 fingerprint of the exact prompt text."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
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
                details_json TEXT NOT NULL
            )
            """
        )
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(experiments)"
            ).fetchall()
        }

        migrations = {
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
        }

        for column, sql in migrations.items():
            if column not in columns:
                connection.execute(sql)

def save_experiment(
    prompt: str,
    result: dict,
    prompt_name: str = "unnamed",
    prompt_version: str = "v1",
) -> int:
    """Persist one completed prompt evaluation and return its ID."""
    prompt_hash = fingerprint_prompt(prompt)
    summary = result["summary"]

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
        prompt_hash
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        json.dumps(result["details"]),
        prompt_name,
        prompt_version,
        prompt_hash,
    ),
        )
        return cursor.lastrowid


def list_experiments(limit: int = 50) -> list[dict]:
    """Return the newest experiment records first."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id, created_at, model, prompt, ticket_count,
                category_accuracy, order_id_accuracy,
                lookup_accuracy, overall_field_accuracy,
                average_latency_ms, total_input_tokens,
                total_output_tokens
            FROM experiments
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_experiment(experiment_id: int) -> dict | None:
    """Return one experiment, including its per-ticket details."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM experiments WHERE id = ?",
            (experiment_id,),
        ).fetchone()

    if row is None:
        return None

    experiment = dict(row)
    experiment["details"] = json.loads(experiment.pop("details_json"))
    return experiment


initialize_database()

