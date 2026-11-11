"""
SQLite storage manager for metadata, file tracking, caching, and generation history.
"""
import sqlite3
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)

class SQLiteStorage:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.DB_PATH
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Files table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                file_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                storage_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_sha256 ON files(sha256);")

            # Template profiles cache
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_profiles (
                sha256 TEXT PRIMARY KEY,
                document_type TEXT,
                profile_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Reference extractions cache
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reference_extractions (
                sha256 TEXT PRIMARY KEY,
                filename TEXT,
                extracted_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Generation history
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS generation_jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                current_step TEXT NOT NULL,
                progress_percentage INTEGER DEFAULT 0,
                template_file_id TEXT,
                reference_file_ids_json TEXT,
                data_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            conn.commit()

    def register_file(self, file_id: str, filename: str, sha256_hash: str, file_type: str, file_size: int, storage_path: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO files (file_id, filename, sha256, file_type, file_size, storage_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (file_id, filename, sha256_hash, file_type, file_size, storage_path, datetime.now(timezone.utc).isoformat()))
            conn.commit()

    def get_file_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE file_id = ?", (file_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_file_by_hash(self, sha256_hash: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE sha256 = ?", (sha256_hash,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_template_profile(self, sha256_hash: str, document_type: str, profile_dict: Dict[str, Any]):
        profile_json = json.dumps(profile_dict)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO template_profiles (sha256, document_type, profile_json, updated_at)
                VALUES (?, ?, ?, ?)
            """, (sha256_hash, document_type, profile_json, datetime.now(timezone.utc).isoformat()))
            conn.commit()

    def get_template_profile(self, sha256_hash: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT profile_json FROM template_profiles WHERE sha256 = ?", (sha256_hash,))
            row = cursor.fetchone()
            if row:
                return json.loads(row["profile_json"])
            return None

    def save_reference_extraction(self, sha256_hash: str, filename: str, extracted_dict: Dict[str, Any]):
        extracted_json = json.dumps(extracted_dict)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO reference_extractions (sha256, filename, extracted_json, updated_at)
                VALUES (?, ?, ?, ?)
            """, (sha256_hash, filename, extracted_json, datetime.now(timezone.utc).isoformat()))
            conn.commit()

    def get_reference_extraction(self, sha256_hash: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT extracted_json FROM reference_extractions WHERE sha256 = ?", (sha256_hash,))
            row = cursor.fetchone()
            if row:
                return json.loads(row["extracted_json"])
            return None

    def save_job(self, job_id: str, status: str, current_step: str, progress: int, data: Dict[str, Any]):
        data_json = json.dumps(data)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO generation_jobs 
                (job_id, status, current_step, progress_percentage, data_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (job_id, status, current_step, progress, data_json, datetime.now(timezone.utc).isoformat()))
            conn.commit()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM generation_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                res = dict(row)
                if res.get("data_json"):
                    res["data"] = json.loads(res["data_json"])
                return res
            return None

storage = SQLiteStorage()
