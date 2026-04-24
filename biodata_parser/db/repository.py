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
        return [self._deserialize_profile_row(dict(row)) for row in rows]

    def get_profile(self, profile_id: int) -> dict | None:
        row = self.connection.execute(
            """
            SELECT *
            FROM profiles
            WHERE id = ?
            """,
            (profile_id,),
        ).fetchone()
        if row is None:
            return None
        return self._deserialize_profile_row(dict(row))

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

    def update_profile(
        self,
        profile_id: int,
        parsed: dict,
        confidence: dict,
        evidence: dict,
        review_status: str,
        manual_edits: dict | None = None,
        raw_text: str | None = None,
        overall_confidence: float | None = None,
    ) -> None:
        current = self.get_profile(profile_id)
        if current is None:
            raise ValueError(f"Profile {profile_id} was not found")

        self.connection.execute(
            """
            UPDATE profiles
            SET parsed_json = ?,
                confidence_json = ?,
                evidence_json = ?,
                overall_confidence = ?,
                review_status = ?,
                manual_edits_json = ?,
                raw_text = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                json.dumps(parsed, ensure_ascii=False),
                json.dumps(confidence, ensure_ascii=False),
                json.dumps(evidence, ensure_ascii=False),
                current["overall_confidence"] if overall_confidence is None else overall_confidence,
                review_status,
                json.dumps(manual_edits or {}, ensure_ascii=False),
                current["raw_text"] if raw_text is None else raw_text,
                _utc_now(),
                profile_id,
            ),
        )
        self.connection.commit()

    def delete_profile(self, profile_id: int) -> dict | None:
        profile = self.get_profile(profile_id)
        if profile is None:
            return None
        self.connection.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        self.connection.commit()
        return profile

    def count_profiles_by_source_path(self, source_file_path: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS count FROM profiles WHERE source_file_path = ?",
            (source_file_path,),
        ).fetchone()
        return int(row["count"]) if row is not None else 0

    def create_log(self, profile_id: int | None, event_type: str, message: str) -> None:
        self.connection.execute(
            """
            INSERT INTO parse_logs (profile_id, event_type, message, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (profile_id, event_type, message, _utc_now()),
        )
        self.connection.commit()

    @staticmethod
    def _deserialize_profile_row(row: dict) -> dict:
        row["parsed_json"] = json.loads(row.get("parsed_json") or "{}")
        row["confidence_json"] = json.loads(row.get("confidence_json") or "{}")
        row["evidence_json"] = json.loads(row.get("evidence_json") or "{}")
        row["manual_edits_json"] = json.loads(row.get("manual_edits_json") or "{}")
        return row
