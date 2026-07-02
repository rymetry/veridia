"""SQLite metadata repository for Evidence Store records."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from evidence_store.errors import EvidenceStoreError

DB_FILENAME = "evidence.sqlite3"
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS evidence_metadata (
    artifact_id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    test_asset_id TEXT NOT NULL,
    verdict TEXT NOT NULL,
    created_at TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_ref TEXT NOT NULL,
    state_diff_ref TEXT NOT NULL,
    log_refs TEXT NOT NULL
)
"""
INSERT_SQL = """
INSERT INTO evidence_metadata (
    artifact_id,
    trace_id,
    run_id,
    test_asset_id,
    verdict,
    created_at,
    schema_version,
    payload_ref,
    state_diff_ref,
    log_refs
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
SELECT_COLUMNS = """
artifact_id,
trace_id,
run_id,
test_asset_id,
verdict,
created_at,
schema_version,
payload_ref,
state_diff_ref,
log_refs
"""
SELECT_BY_ARTIFACT_ID_SQL = (
    "SELECT artifact_id, trace_id, run_id, test_asset_id, verdict, created_at, schema_version, "
    "payload_ref, state_diff_ref, log_refs FROM evidence_metadata WHERE artifact_id = ?"
)
SELECT_BY_TRACE_ID_SQL = (
    "SELECT artifact_id, trace_id, run_id, test_asset_id, verdict, created_at, schema_version, "
    "payload_ref, state_diff_ref, log_refs FROM evidence_metadata WHERE trace_id = ? "
    "ORDER BY created_at, artifact_id"
)
SELECT_BY_RUN_ID_SQL = (
    "SELECT artifact_id, trace_id, run_id, test_asset_id, verdict, created_at, schema_version, "
    "payload_ref, state_diff_ref, log_refs FROM evidence_metadata WHERE run_id = ? "
    "ORDER BY created_at, artifact_id"
)
SELECT_BY_TEST_ASSET_ID_SQL = (
    "SELECT artifact_id, trace_id, run_id, test_asset_id, verdict, created_at, schema_version, "
    "payload_ref, state_diff_ref, log_refs FROM evidence_metadata WHERE test_asset_id = ? "
    "ORDER BY created_at, artifact_id"
)


@dataclass(frozen=True)
class EvidenceMetadata:
    """Searchable metadata for one ExecutionEvidence artifact."""

    artifact_id: str
    trace_id: str
    run_id: str
    test_asset_id: str
    verdict: str
    created_at: str
    schema_version: str
    payload_ref: str
    state_diff_ref: str
    log_refs: tuple[str, ...]


class SqliteEvidenceMetadataRepository:
    """SQLite implementation of the Evidence metadata repository boundary."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @classmethod
    def under_root(cls, root: Path) -> SqliteEvidenceMetadataRepository:
        return cls(Path(root) / DB_FILENAME)

    def save(self, metadata: EvidenceMetadata) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    INSERT_SQL,
                    (
                        metadata.artifact_id,
                        metadata.trace_id,
                        metadata.run_id,
                        metadata.test_asset_id,
                        metadata.verdict,
                        metadata.created_at,
                        metadata.schema_version,
                        metadata.payload_ref,
                        metadata.state_diff_ref,
                        json.dumps(list(metadata.log_refs), sort_keys=True),
                    ),
                )
        except sqlite3.Error as exc:
            raise EvidenceStoreError(
                f"failed to save evidence metadata for {metadata.artifact_id}: {exc}"
            ) from exc

    def get_by_artifact_id(self, artifact_id: str) -> EvidenceMetadata | None:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    SELECT_BY_ARTIFACT_ID_SQL,
                    (artifact_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise EvidenceStoreError(
                f"failed to read evidence metadata {artifact_id}: {exc}"
            ) from exc
        if row is None:
            return None
        return _metadata_from_row(row)

    def find_by_trace_id(self, trace_id: str) -> tuple[EvidenceMetadata, ...]:
        return self._find_many(
            SELECT_BY_TRACE_ID_SQL,
            trace_id,
            f"failed to query evidence metadata for trace_id {trace_id}",
        )

    def find_by_run_id(self, run_id: str) -> tuple[EvidenceMetadata, ...]:
        return self._find_many(
            SELECT_BY_RUN_ID_SQL,
            run_id,
            f"failed to query evidence metadata for run_id {run_id}",
        )

    def find_by_test_asset_id(self, test_asset_id: str) -> tuple[EvidenceMetadata, ...]:
        return self._find_many(
            SELECT_BY_TEST_ASSET_ID_SQL,
            test_asset_id,
            f"failed to query evidence metadata for test_asset_id {test_asset_id}",
        )

    def _find_many(
        self,
        sql: str,
        value: str,
        error_message: str,
    ) -> tuple[EvidenceMetadata, ...]:
        try:
            with self._connect() as connection:
                rows = connection.execute(sql, (value,)).fetchall()
        except sqlite3.Error as exc:
            raise EvidenceStoreError(f"{error_message}: {exc}") from exc
        return tuple(_metadata_from_row(row) for row in rows)

    def _ensure_schema(self) -> None:
        try:
            with self._connect() as connection:
                connection.execute(SCHEMA_SQL)
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS evidence_metadata_trace_id_idx "
                    "ON evidence_metadata (trace_id)"
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS evidence_metadata_run_id_idx "
                    "ON evidence_metadata (run_id)"
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS evidence_metadata_test_asset_id_idx "
                    "ON evidence_metadata (test_asset_id)"
                )
        except sqlite3.Error as exc:
            raise EvidenceStoreError(f"failed to initialize evidence metadata DB: {exc}") from exc

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)


def _metadata_from_row(row: tuple[str, ...]) -> EvidenceMetadata:
    log_refs = json.loads(row[9])
    if not isinstance(log_refs, list) or not all(isinstance(ref, str) for ref in log_refs):
        raise EvidenceStoreError(f"invalid log_refs metadata for {row[0]}")
    return EvidenceMetadata(
        artifact_id=row[0],
        trace_id=row[1],
        run_id=row[2],
        test_asset_id=row[3],
        verdict=row[4],
        created_at=row[5],
        schema_version=row[6],
        payload_ref=row[7],
        state_diff_ref=row[8],
        log_refs=tuple(log_refs),
    )
