from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, UTC
from sqlite3 import Connection


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class ProfileRecord:
    source_file_name: str
    source_file_path: str
    extraction_method: str
    raw_text: str
    parsed: dict
    confidence: dict
    evidence: dict
    overall_confidence: float
    review_status: str
    manual_edits: dict | None = None


class ProfileRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def list_profiles(self) -> list[dict]:
        rows = self.connection.execute(
            """
            SELECT *
            FROM profiles
            ORDER BY updated_at DESC, id DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def create_profile(self, record: ProfileRecord) -> int:
        now = _utc_now()
        cursor = self.connection.execute(
            """
            INSERT INTO profiles (
                source_file_name,
                source_file_path,
                extraction_method,
                raw_text,
                parsed_json,
                confidence_json,
                evidence_json,
                overall_confidence,
                review_status,
                manual_edits_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.source_file_name,
                record.source_file_path,
                record.extraction_method,
                record.raw_text,
                json.dumps(record.parsed, ensure_ascii=False),
                json.dumps(record.confidence, ensure_ascii=False),
                json.dumps(record.evidence, ensure_ascii=False),
                record.overall_confidence,
                record.review_status,
                json.dumps(record.manual_edits or {}, ensure_ascii=False),
                now,
                now,
            ),
        )
        self.connection.commit()
        return int(cursor.lastrowid)
