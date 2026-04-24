from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from biodata_parser.constants import (
    MIN_IMPORT_OVERALL_CONFIDENCE,
    REVIEW_STATUS_FAILED,
    REVIEW_STATUS_NEEDS_REVIEW,
    REVIEW_STATUS_PARSED,
)
from biodata_parser.db.repository import ProfileRecord, ProfileRepository
from biodata_parser.parsing.field_config import load_field_config
from biodata_parser.parsing.field_extractor import extract_fields
from biodata_parser.parsing.pdf_text_extractor import extract_text_from_pdf
from biodata_parser.paths import AppPaths


class ImportService:
    def __init__(self, repository: ProfileRepository, app_paths: AppPaths) -> None:
        self.repository = repository
        self.app_paths = app_paths

    def import_pdf(self, file_path: str) -> dict:
        source = Path(file_path)
        if source.suffix.lower() != ".pdf":
            raise ValueError("Only PDF files are supported")
        if not source.exists():
            raise FileNotFoundError(f"Missing PDF: {file_path}")

        copied_path = self._copy_pdf_to_storage(source)
        extraction = extract_text_from_pdf(str(copied_path))
        field_config = load_field_config(self.app_paths.field_config_path)
        extraction_result = extract_fields(extraction["text"], field_config)
        review_status = self._determine_review_status(extraction["method"], extraction_result)

        profile_id = self.repository.create_profile(
            ProfileRecord(
                source_file_name=source.name,
                source_file_path=str(copied_path),
                extraction_method=extraction["method"],
                raw_text=extraction["text"],
                parsed=extraction_result["values"],
                confidence=extraction_result["confidence"],
                evidence=extraction_result["evidence"],
                overall_confidence=extraction_result["overall_confidence"],
                review_status=review_status,
            )
        )
        self.repository.create_log(profile_id, "import", f"Imported {source.name} via {extraction['method']}")
        return self.repository.get_profile(profile_id) or {}

    def import_folder(self, folder_path: str) -> list[dict]:
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Missing folder: {folder_path}")
        results: list[dict] = []
        for pdf_path in sorted(folder.glob("*.pdf")):
            try:
                results.append(self.import_pdf(str(pdf_path)))
            except Exception as exc:
                self.repository.create_log(None, "import_error", f"{pdf_path.name}: {exc}")
        return results

    def reparse_profile(self, profile_id: int, overwrite_manual_edits: bool) -> dict:
        profile = self.repository.get_profile(profile_id)
        if profile is None:
            raise ValueError(f"Profile {profile_id} was not found")

        extraction = extract_text_from_pdf(profile["source_file_path"])
        field_config = load_field_config(self.app_paths.field_config_path)
        extraction_result = extract_fields(extraction["text"], field_config)
        parsed = extraction_result["values"]
        manual_edits = {} if overwrite_manual_edits else profile["manual_edits_json"]
        if not overwrite_manual_edits:
            parsed = {**parsed, **profile["manual_edits_json"]}

        review_status = self._determine_review_status(extraction["method"], extraction_result)
        self.repository.update_profile(
            profile_id,
            parsed=parsed,
            confidence=extraction_result["confidence"],
            evidence=extraction_result["evidence"],
            review_status=review_status,
            manual_edits=manual_edits,
            raw_text=extraction["text"],
            overall_confidence=extraction_result["overall_confidence"],
        )
        self.repository.create_log(profile_id, "reparse", f"Re-parsed record {profile_id}")
        return self.repository.get_profile(profile_id) or {}

    def _copy_pdf_to_storage(self, source: Path) -> Path:
        destination = self.app_paths.uploads_dir / f"{uuid.uuid4().hex}_{source.name}"
        shutil.copy2(source, destination)
        return destination

    @staticmethod
    def _determine_review_status(extraction_method: str, extraction_result: dict) -> str:
        if extraction_method == "failed":
            return REVIEW_STATUS_FAILED
        if extraction_result["missing_required"]:
            return REVIEW_STATUS_NEEDS_REVIEW
        if extraction_result["overall_confidence"] < MIN_IMPORT_OVERALL_CONFIDENCE:
            return REVIEW_STATUS_NEEDS_REVIEW
        return REVIEW_STATUS_PARSED
