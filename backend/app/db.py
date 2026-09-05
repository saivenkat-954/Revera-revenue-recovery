from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DB_PATH = DATA_DIR / "recoveros.db"


def _now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


def _ensure_column(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:
    columns = {
        row["name"]
        for row in conn.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    }

    if column not in columns:
        conn.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def init_db() -> None:
    conn = _get_connection()

    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS recovery_cases (
                id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                event_type TEXT,
                amount REAL NOT NULL DEFAULT 0,
                currency TEXT NOT NULL DEFAULT 'INR',
                payment_method TEXT,
                failure_reason TEXT,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                successful_payments INTEGER NOT NULL DEFAULT 0,
                failed_payments INTEGER NOT NULL DEFAULT 0,
                recovery_probability REAL NOT NULL DEFAULT 0,
                risk_score REAL NOT NULL DEFAULT 0,
                expected_recovery REAL NOT NULL DEFAULT 0,
                recommended_action TEXT,
                status TEXT NOT NULL DEFAULT 'at_risk',
                recovered_amount REAL NOT NULL DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT NOT NULL,
                details TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(case_id)
                    REFERENCES recovery_cases(id)
            );

            CREATE TABLE IF NOT EXISTS recovery_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                action TEXT NOT NULL,
                amount REAL NOT NULL DEFAULT 0,
                currency TEXT NOT NULL DEFAULT 'INR',
                provider TEXT,
                provider_id TEXT,
                payment_link TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                recovered_amount REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(case_id)
                    REFERENCES recovery_cases(id)
            );

            CREATE TABLE IF NOT EXISTS webhook_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                event_type TEXT,
                case_id TEXT,
                payload TEXT,
                processed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_recovery_actions_case
            ON recovery_actions(case_id);

            CREATE INDEX IF NOT EXISTS idx_recovery_actions_provider
            ON recovery_actions(provider_id);

            CREATE INDEX IF NOT EXISTS idx_recovery_actions_status
            ON recovery_actions(status);

            CREATE INDEX IF NOT EXISTS idx_audit_case
            ON audit_events(case_id);

            CREATE INDEX IF NOT EXISTS idx_webhook_event
            ON webhook_events(event_id);
            """
        )

        _ensure_column(
            conn,
            "recovery_cases",
            "currency",
            "TEXT NOT NULL DEFAULT 'INR'",
        )

        _ensure_column(
            conn,
            "recovery_cases",
            "payment_method",
            "TEXT",
        )

        _ensure_column(
            conn,
            "recovery_cases",
            "expected_recovery",
            "REAL NOT NULL DEFAULT 0",
        )

        _ensure_column(
            conn,
            "recovery_cases",
            "recovered_amount",
            "REAL NOT NULL DEFAULT 0",
        )

        _ensure_column(
            conn,
            "recovery_cases",
            "created_at",
            "TEXT",
        )

        _ensure_column(
            conn,
            "recovery_cases",
            "updated_at",
            "TEXT",
        )

        conn.commit()

    finally:
        conn.close()


def upsert_case(
    case_data: dict[str, Any],
) -> dict[str, Any]:
    now = _now()

    case_id = str(
        case_data.get(
            "id",
            case_data.get(
                "case_id"
            ),
        )
    )

    customer_id = str(
        case_data.get(
            "customer_id",
            "",
        )
    )

    amount = float(
        case_data.get(
            "amount",
            0,
        )
        or 0
    )

    currency = str(
        case_data.get(
            "currency",
            "INR",
        )
        or "INR"
    ).upper()

    event_type = case_data.get(
        "event_type",
        "payment.failed",
    )

    payment_method = case_data.get(
        "payment_method"
    )

    failure_reason = case_data.get(
        "failure_reason"
    )

    attempt_count = int(
        case_data.get(
            "attempt_count",
            case_data.get(
                "attempts",
                0,
            ),
        )
        or 0
    )

    successful_payments = int(
        case_data.get(
            "successful_payments",
            case_data.get(
                "successes",
                0,
            ),
        )
        or 0
    )

    failed_payments = int(
        case_data.get(
            "failed_payments",
            case_data.get(
                "failures",
                0,
            ),
        )
        or 0
    )

    recovery_probability = float(
        case_data.get(
            "recovery_probability",
            0,
        )
        or 0
    )

    risk_score = float(
        case_data.get(
            "risk_score",
            0,
        )
        or 0
    )

    expected_recovery = float(
        case_data.get(
            "expected_recovery",
            0,
        )
        or 0
    )

    recommended_action = case_data.get(
        "recommended_action"
    )

    status = case_data.get(
        "status",
        "at_risk",
    )

    recovered_amount = float(
        case_data.get(
            "recovered_amount",
            0,
        )
        or 0
    )

    conn = _get_connection()

    try:
        existing = conn.execute(
            """
            SELECT created_at
            FROM recovery_cases
            WHERE id = ?
            """,
            (case_id,),
        ).fetchone()

        created_at = (
            existing["created_at"]
            if existing and existing["created_at"]
            else case_data.get(
                "created_at",
                now,
            )
        )

        conn.execute(
            """
            INSERT INTO recovery_cases (
                id,
                customer_id,
                event_type,
                amount,
                currency,
                payment_method,
                failure_reason,
                attempt_count,
                successful_payments,
                failed_payments,
                recovery_probability,
                risk_score,
                expected_recovery,
                recommended_action,
                status,
                recovered_amount,
                created_at,
                updated_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(id) DO UPDATE SET
                customer_id = excluded.customer_id,
                event_type = excluded.event_type,
                amount = excluded.amount,
                currency = excluded.currency,
                payment_method = excluded.payment_method,
                failure_reason = excluded.failure_reason,
                attempt_count = excluded.attempt_count,
                successful_payments = excluded.successful_payments,
                failed_payments = excluded.failed_payments,
                recovery_probability = excluded.recovery_probability,
                risk_score = excluded.risk_score,
                expected_recovery = excluded.expected_recovery,
                recommended_action = excluded.recommended_action,
                status = CASE
                    WHEN recovery_cases.status IN (
                        'recovered',
                        'partially_recovered'
                    )
                    THEN recovery_cases.status
                    ELSE excluded.status
                END,
                recovered_amount = MAX(
                    recovery_cases.recovered_amount,
                    excluded.recovered_amount
                ),
                updated_at = excluded.updated_at
            """,
            (
                case_id,
                customer_id,
                event_type,
                amount,
                currency,
                payment_method,
                failure_reason,
                attempt_count,
                successful_payments,
                failed_payments,
                recovery_probability,
                risk_score,
                expected_recovery,
                recommended_action,
                status,
                recovered_amount,
                created_at,
                now,
            ),
        )

        conn.commit()

        row = conn.execute(
            """
            SELECT *
            FROM recovery_cases
            WHERE id = ?
            """,
            (case_id,),
        ).fetchone()

        return dict(row)

    finally:
        conn.close()


def get_cases() -> list[dict[str, Any]]:
    conn = _get_connection()

    try:
        rows = conn.execute(
            """
            SELECT *
            FROM recovery_cases
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        conn.close()


def get_case(
    case_id: str,
) -> dict[str, Any] | None:
    conn = _get_connection()

    try:
        row = conn.execute(
            """
            SELECT *
            FROM recovery_cases
            WHERE id = ?
            """,
            (case_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        conn.close()


def update_case_status(
    case_id: str,
    status: str,
) -> None:
    conn = _get_connection()

    try:
        conn.execute(
            """
            UPDATE recovery_cases
            SET status = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                status,
                _now(),
                case_id,
            ),
        )

        conn.commit()

    finally:
        conn.close()


def mark_case_recovered(
    case_id: str,
    recovered_amount: float,
) -> dict[str, Any] | None:
    conn = _get_connection()

    try:
        row = conn.execute(
            """
            SELECT amount
            FROM recovery_cases
            WHERE id = ?
            """,
            (case_id,),
        ).fetchone()

        if not row:
            return None

        case_amount = float(
            row["amount"] or 0
        )

        current = conn.execute(
            """
            SELECT recovered_amount
            FROM recovery_cases
            WHERE id = ?
            """,
            (case_id,),
        ).fetchone()

        previous = float(
            current["recovered_amount"]
            if current
            else 0
        )

        total = min(
            case_amount,
            max(
                previous,
                float(recovered_amount),
            ),
        )

        if total >= case_amount:
            status = "recovered"
        elif total > 0:
            status = "partially_recovered"
        else:
            status = "at_risk"

        conn.execute(
            """
            UPDATE recovery_cases
            SET recovered_amount = ?,
                status = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                total,
                status,
                _now(),
                case_id,
            ),
        )

        conn.commit()

        updated = conn.execute(
            """
            SELECT *
            FROM recovery_cases
            WHERE id = ?
            """,
            (case_id,),
        ).fetchone()

        return dict(updated) if updated else None

    finally:
        conn.close()


def add_audit_event(
    case_id: str,
    event_type: str,
    actor: str,
    details: Any = None,
) -> dict[str, Any]:
    conn = _get_connection()

    try:
        if isinstance(details, str):
            serialized = details
        else:
            serialized = json.dumps(
                details,
                ensure_ascii=False,
                default=str,
            )

        cursor = conn.execute(
            """
            INSERT INTO audit_events (
                case_id,
                event_type,
                actor,
                details,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                case_id,
                event_type,
                actor,
                serialized,
                _now(),
            ),
        )

        conn.commit()

        return {
            "id": cursor.lastrowid,
            "case_id": case_id,
            "event_type": event_type,
            "actor": actor,
            "details": serialized,
        }

    finally:
        conn.close()


def get_audit_events(
    limit: int = 100,
) -> list[dict[str, Any]]:
    conn = _get_connection()

    try:
        rows = conn.execute(
            """
            SELECT *
            FROM audit_events
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        conn.close()


def get_case_audit_events(
    case_id: str,
) -> list[dict[str, Any]]:
    conn = _get_connection()

    try:
        rows = conn.execute(
            """
            SELECT *
            FROM audit_events
            WHERE case_id = ?
            ORDER BY id ASC
            """,
            (case_id,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        conn.close()


def create_recovery_action(
    case_id: str,
    customer_id: str,
    action: str,
    amount: float,
    currency: str,
    provider: str | None = None,
    provider_id: str | None = None,
    payment_link: str | None = None,
    status: str = "pending",
    recovered_amount: float = 0,
) -> int:
    now = _now()

    conn = _get_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO recovery_actions (
                case_id,
                customer_id,
                action,
                amount,
                currency,
                provider,
                provider_id,
                payment_link,
                status,
                recovered_amount,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                customer_id,
                action,
                float(amount),
                currency.upper(),
                provider,
                provider_id,
                payment_link,
                status,
                float(recovered_amount),
                now,
                now,
            ),
        )

        conn.commit()

        return int(
            cursor.lastrowid
        )

    finally:
        conn.close()


def update_recovery_action_status(
    provider_id: str,
    status: str,
    recovered_amount: float | None = None,
) -> dict[str, Any] | None:
    conn = _get_connection()

    try:
        if recovered_amount is None:
            conn.execute(
                """
                UPDATE recovery_actions
                SET status = ?,
                    updated_at = ?
                WHERE provider_id = ?
                """,
                (
                    status,
                    _now(),
                    provider_id,
                ),
            )
        else:
            conn.execute(
                """
                UPDATE recovery_actions
                SET status = ?,
                    recovered_amount = ?,
                    updated_at = ?
                WHERE provider_id = ?
                """,
                (
                    status,
                    float(recovered_amount),
                    _now(),
                    provider_id,
                ),
            )

        conn.commit()

        row = conn.execute(
            """
            SELECT *
            FROM recovery_actions
            WHERE provider_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (provider_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        conn.close()


def get_recovery_actions(
    limit: int = 100,
) -> list[dict[str, Any]]:
    conn = _get_connection()

    try:
        rows = conn.execute(
            """
            SELECT *
            FROM recovery_actions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        conn.close()


def get_active_recovery_action(
    case_id: str,
) -> dict[str, Any] | None:
    conn = _get_connection()

    try:
        row = conn.execute(
            """
            SELECT *
            FROM recovery_actions
            WHERE case_id = ?
              AND status IN (
                  'issued',
                  'pending',
                  'partially_paid'
              )
            ORDER BY id DESC
            LIMIT 1
            """,
            (case_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        conn.close()


def get_recovery_action_by_provider_id(
    provider_id: str,
) -> dict[str, Any] | None:
    conn = _get_connection()

    try:
        row = conn.execute(
            """
            SELECT *
            FROM recovery_actions
            WHERE provider_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (provider_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        conn.close()


def store_webhook_event(
    event_id: str,
    event_type: str,
    payload: Any,
    case_id: str | None = None,
) -> bool:
    conn = _get_connection()

    try:
        serialized = (
            payload
            if isinstance(payload, str)
            else json.dumps(
                payload,
                ensure_ascii=False,
                default=str,
            )
        )

        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO webhook_events (
                event_id,
                event_type,
                case_id,
                payload,
                processed,
                created_at
            )
            VALUES (?, ?, ?, ?, 0, ?)
            """,
            (
                event_id,
                event_type,
                case_id,
                serialized,
                _now(),
            ),
        )

        conn.commit()

        return cursor.rowcount == 1

    finally:
        conn.close()


def mark_webhook_processed(
    event_id: str,
) -> None:
    conn = _get_connection()

    try:
        conn.execute(
            """
            UPDATE webhook_events
            SET processed = 1
            WHERE event_id = ?
            """,
            (event_id,),
        )

        conn.commit()

    finally:
        conn.close()


def get_recovery_analytics() -> dict[str, Any]:
    conn = _get_connection()

    try:
        attempts = conn.execute(
            """
            SELECT COUNT(*)
            AS count
            FROM recovery_actions
            """
        ).fetchone()

        attempted_value = conn.execute(
            """
            SELECT COALESCE(
                SUM(amount),
                0
            ) AS value
            FROM recovery_actions
            """
        ).fetchone()

        verified = conn.execute(
            """
            SELECT COALESCE(
                SUM(recovered_amount),
                0
            ) AS value
            FROM recovery_actions
            WHERE status = 'paid'
            """
        ).fetchone()

        partial = conn.execute(
            """
            SELECT COALESCE(
                SUM(recovered_amount),
                0
            ) AS value
            FROM recovery_actions
            WHERE status = 'partially_paid'
            """
        ).fetchone()

        active = conn.execute(
            """
            SELECT COALESCE(
                SUM(amount),
                0
            ) AS value
            FROM recovery_actions
            WHERE status IN (
                'issued',
                'pending'
            )
            """
        ).fetchone()

        return {
            "recovery_attempts": int(
                attempts["count"] or 0
            ),
            "attempted_recovery_value": float(
                attempted_value["value"] or 0
            ),
            "verified_recovered": float(
                verified["value"] or 0
            ),
            "partial_verified_recovered": float(
                partial["value"] or 0
            ),
            "active_recovery_value": float(
                active["value"] or 0
            ),
        }

    finally:
        conn.close()