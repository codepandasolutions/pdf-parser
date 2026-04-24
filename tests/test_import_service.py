from __future__ import annotations

import shutil
from pathlib import Path

from biodata_parser.db.database import connect_database, initialize_database
from biodata_parser.db.repository import ProfileRecord, ProfileRepository
from biodata_parser.paths import AppPaths
from biodata_parser.services.import_service import ImportService


def _build_app_paths(tmp_path: Path) -> AppPaths:
    root = tmp_path / "app_data"
    config_dir = root / "config"
    uploads_dir = root / "uploads" / "copied_pdf_files"
    logs_dir = root / "logs"
    exports_dir = root / "exports"
    for directory in (config_dir, uploads_dir, logs_dir, exports_dir):
        directory.mkdir(parents=True, exist_ok=True)

    field_config_path = config_dir / "fields.yaml"
    shutil.copy2(Path("config/default_fields.yaml"), field_config_path)

    return AppPaths(
        root=root,
        config_dir=config_dir,
        uploads_dir=uploads_dir,
        logs_dir=logs_dir,
        exports_dir=exports_dir,
        database_path=root / "app.db",
        field_config_path=field_config_path,
        log_file_path=logs_dir / "app.log",
    )


def _build_service(tmp_path: Path) -> tuple[ImportService, ProfileRepository]:
    app_paths = _build_app_paths(tmp_path)
    connection = connect_database(app_paths.database_path)
    initialize_database(connection)
    repository = ProfileRepository(connection)
    service = ImportService(repository, app_paths)
    return service, repository


def test_save_manual_edits_marks_record_reviewed(tmp_path: Path) -> None:
    service, repository = _build_service(tmp_path)
    profile_id = repository.create_profile(
        ProfileRecord(
            source_file_name="sample.pdf",
            source_file_path=str(tmp_path / "sample.pdf"),
            extraction_method="pymupdf",
            raw_text="Name: Rahul Sharma",
            parsed={"full_name": "Rahul Sharma"},
            confidence={"full_name": 0.9},
            evidence={"full_name": {"method": "label"}},
            overall_confidence=0.9,
            review_status="Parsed",
        )
    )

    updated = service.save_manual_edits(profile_id, {"full_name": "Rahul S. Sharma"}, mark_reviewed=True)

    assert updated["parsed_json"]["full_name"] == "Rahul S. Sharma"
    assert updated["manual_edits_json"]["full_name"] == "Rahul S. Sharma"
    assert updated["review_status"] == "Reviewed"


def test_reparse_profile_preserves_manual_edits_when_requested(tmp_path: Path, monkeypatch) -> None:
    service, repository = _build_service(tmp_path)
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")
    profile_id = repository.create_profile(
        ProfileRecord(
            source_file_name="sample.pdf",
            source_file_path=str(pdf_path),
            extraction_method="pymupdf",
            raw_text="Name: Rahul Sharma",
            parsed={"full_name": "Rahul Sharma", "education": "B.Tech"},
            confidence={"full_name": 0.9, "education": 0.9},
            evidence={"full_name": {"method": "label"}, "education": {"method": "label"}},
            overall_confidence=0.9,
            review_status="Reviewed",
            manual_edits={"full_name": "Rahul S. Sharma"},
        )
    )

    def fake_extract_text_from_pdf(_file_path: str) -> dict:
        return {
            "text": "Name: Rahul Sharma\nEducation: M.Tech",
            "method": "pymupdf",
            "pages": [{"page": 1, "text": "Name: Rahul Sharma\nEducation: M.Tech"}],
            "errors": [],
        }

    monkeypatch.setattr("biodata_parser.services.import_service.extract_text_from_pdf", fake_extract_text_from_pdf)

    updated = service.reparse_profile(profile_id, overwrite_manual_edits=False)

    assert updated["parsed_json"]["full_name"] == "Rahul S. Sharma"
    assert updated["parsed_json"]["education"] == "M.Tech"
    assert updated["manual_edits_json"]["full_name"] == "Rahul S. Sharma"
    assert updated["review_status"] == "Reviewed"
