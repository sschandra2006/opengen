"""
Persistent SQLite Job Ledger for tracking per-generation status, artifacts,
and isolated cost telemetry across all 4 engines.
"""
import json
import sqlite3
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from opengen.config import settings
from opengen.domain.job import JobRecord, JobStatus

logger = logging.getLogger(__name__)


class JobStore:
    """Thread-safe SQLite store persisting per-generation JobRecord entries."""

    def __init__(self, db_path: Optional[Path] = None):
        self._explicit_db_path = db_path

    @property
    def db_path(self) -> Path:
        return self._explicit_db_path or settings.JOBS_DB_PATH

    def _connect(self) -> sqlite3.Connection:
        p = self.db_path
        p.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(p), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                engine TEXT NOT NULL,
                status TEXT NOT NULL,
                current_step TEXT NOT NULL,
                progress_percentage INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                artifacts_json TEXT NOT NULL,
                telemetry_json TEXT NOT NULL,
                error_message TEXT,
                clarifications_json TEXT,
                metadata_json TEXT NOT NULL
            )
        """)
        conn.commit()
        return conn

    def save_job(self, record: JobRecord):
        record.updated_at = datetime.now(timezone.utc)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    job_id, engine, status, current_step, progress_percentage,
                    created_at, updated_at, artifacts_json, telemetry_json,
                    error_message, clarifications_json, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    status=excluded.status,
                    current_step=excluded.current_step,
                    progress_percentage=excluded.progress_percentage,
                    updated_at=excluded.updated_at,
                    artifacts_json=excluded.artifacts_json,
                    telemetry_json=excluded.telemetry_json,
                    error_message=excluded.error_message,
                    clarifications_json=excluded.clarifications_json,
                    metadata_json=excluded.metadata_json
                """,
                (
                    record.job_id,
                    record.engine,
                    record.status.value,
                    record.current_step,
                    record.progress_percentage,
                    record.created_at.isoformat(),
                    record.updated_at.isoformat(),
                    json.dumps(record.artifacts),
                    json.dumps(record.telemetry),
                    record.error_message,
                    json.dumps(record.clarifications_needed) if record.clarifications_needed is not None else None,
                    json.dumps(record.metadata),
                ),
            )
            conn.commit()

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            if not row:
                return None
            return JobRecord(
                job_id=row["job_id"],
                engine=row["engine"],
                status=JobStatus(row["status"]),
                current_step=row["current_step"],
                progress_percentage=row["progress_percentage"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                artifacts=json.loads(row["artifacts_json"]),
                telemetry=json.loads(row["telemetry_json"]),
                error_message=row["error_message"],
                clarifications_needed=json.loads(row["clarifications_json"]) if row["clarifications_json"] else None,
                metadata=json.loads(row["metadata_json"]),
            )


job_store = JobStore()
