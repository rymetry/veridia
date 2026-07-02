"""SQLite repository for Trace Store records."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from trace_store.errors import TraceStoreError
from trace_store.records import TraceRecord

DB_FILENAME = "trace.sqlite3"
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS trace_records (
    run_id TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    parent_span_id TEXT,
    sequence INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    latency_ms INTEGER,
    redacted_args TEXT NOT NULL,
    result_summary TEXT,
    error_summary TEXT,
    PRIMARY KEY (run_id, trace_id, sequence)
)
"""
INSERT_SQL = """
INSERT INTO trace_records (
    run_id,
    trace_id,
    span_id,
    parent_span_id,
    sequence,
    event_type,
    name,
    status,
    started_at,
    ended_at,
    latency_ms,
    redacted_args,
    result_summary,
    error_summary
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
SELECT_COLUMNS = """
run_id,
trace_id,
span_id,
parent_span_id,
sequence,
event_type,
name,
status,
started_at,
ended_at,
latency_ms,
redacted_args,
result_summary,
error_summary
"""
SELECT_BY_TRACE_ID_SQL = (
    "SELECT run_id, trace_id, span_id, parent_span_id, sequence, event_type, name, status, "
    "started_at, ended_at, latency_ms, redacted_args, result_summary, error_summary "
    "FROM trace_records WHERE trace_id = ? ORDER BY sequence, started_at, span_id"
)
SELECT_BY_RUN_ID_SQL = (
    "SELECT run_id, trace_id, span_id, parent_span_id, sequence, event_type, name, status, "
    "started_at, ended_at, latency_ms, redacted_args, result_summary, error_summary "
    "FROM trace_records WHERE run_id = ? ORDER BY sequence, started_at, span_id"
)


class SqliteTraceRecordRepository:
    """SQLite implementation of the Trace Store repository boundary."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @classmethod
    def under_root(cls, root: Path) -> SqliteTraceRecordRepository:
        return cls(Path(root) / DB_FILENAME)

    def save(self, record: TraceRecord) -> None:
        params = _record_params(record)
        try:
            with self._connect() as connection:
                connection.execute(INSERT_SQL, params)
        except sqlite3.Error as exc:
            raise TraceStoreError(
                f"failed to save trace record {record.trace_id}/{record.sequence}: {exc}"
            ) from exc

    def find_by_trace_id(self, trace_id: str) -> tuple[TraceRecord, ...]:
        return self._find_many(
            SELECT_BY_TRACE_ID_SQL,
            trace_id,
            f"failed to query trace records for trace_id {trace_id}",
        )

    def find_by_run_id(self, run_id: str) -> tuple[TraceRecord, ...]:
        return self._find_many(
            SELECT_BY_RUN_ID_SQL,
            run_id,
            f"failed to query trace records for run_id {run_id}",
        )

    def _find_many(
        self,
        sql: str,
        value: str,
        error_message: str,
    ) -> tuple[TraceRecord, ...]:
        try:
            with self._connect() as connection:
                rows = connection.execute(sql, (value,)).fetchall()
        except sqlite3.Error as exc:
            raise TraceStoreError(f"{error_message}: {exc}") from exc
        return tuple(_record_from_row(row) for row in rows)

    def _ensure_schema(self) -> None:
        try:
            with self._connect() as connection:
                connection.execute(SCHEMA_SQL)
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS trace_records_trace_id_idx "
                    "ON trace_records (trace_id)"
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS trace_records_run_id_idx ON trace_records (run_id)"
                )
        except sqlite3.Error as exc:
            raise TraceStoreError(f"failed to initialize trace record DB: {exc}") from exc

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)


def _record_params(record: TraceRecord) -> tuple[Any, ...]:
    try:
        redacted_args = json.dumps(record.redacted_args, ensure_ascii=False, sort_keys=True)
    except TypeError as exc:
        raise TraceStoreError("redacted_args must be JSON-serializable") from exc
    return (
        record.run_id,
        record.trace_id,
        record.span_id,
        record.parent_span_id,
        record.sequence,
        record.event_type,
        record.name,
        record.status,
        record.started_at,
        record.ended_at,
        record.latency_ms,
        redacted_args,
        record.result_summary,
        record.error_summary,
    )


def _record_from_row(row: tuple[Any, ...]) -> TraceRecord:
    redacted_args = json.loads(row[11])
    if not isinstance(redacted_args, dict):
        raise TraceStoreError(f"invalid redacted_args metadata for {row[1]}/{row[4]}")
    return TraceRecord(
        run_id=row[0],
        trace_id=row[1],
        span_id=row[2],
        parent_span_id=row[3],
        sequence=row[4],
        event_type=row[5],
        name=row[6],
        status=row[7],
        started_at=row[8],
        ended_at=row[9],
        latency_ms=row[10],
        redacted_args=redacted_args,
        result_summary=row[12],
        error_summary=row[13],
    )
