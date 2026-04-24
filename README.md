# Biodata Parser Desktop

`Biodata Parser Desktop` is a local-first Windows desktop application for importing arranged-marriage biodata PDFs, extracting structured fields using deterministic parsing rules, reviewing the extracted values, and exporting records to CSV.

## Principles

- No AI, no cloud parsing, no external biodata upload.
- Configurable field extraction driven by YAML.
- Manual review always wins over automatic parsing.
- User data lives outside the install directory so updates preserve it.

## Supported Environment

- Development: macOS is acceptable.
- Release target: Windows 11.
- Release builds: GitHub Actions Windows runners.
- Release validation: a real Windows laptop before sharing with end users.

## Planned Features

- Import single PDFs and folders of PDFs.
- Deterministic extraction via PyMuPDF, `pdfplumber`, and optional OCR.
- Editable review screen with confidence metadata and raw text.
- SQLite-backed local storage.
- View source PDF from the records table.
- Delete records with confirmation.
- CSV export using configured field order.
- Update checks via public GitHub Releases.

## Tech Stack

- Python 3.11+
- PySide6
- SQLite
- PyMuPDF
- `pdfplumber`
- Optional OCR via `pytesseract` and `pdf2image`
- PyInstaller for Windows packaging

## Project Layout

```text
biodata-parser-desktop/
├─ .github/workflows/
├─ biodata_parser/
│  ├─ db/
│  ├─ parsing/
│  ├─ services/
│  ├─ ui/
│  └─ utils/
├─ config/
├─ tests/
├─ app.py
├─ pyproject.toml
├─ requirements.txt
└─ README.md
```

## Local Development

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
pip install pytest
```

### 3. Run the app

```bash
python app.py
```

## macOS Developer Workflow

macOS is supported as a development environment even though Windows remains the only end-user release target for now.

Use the helper launcher to keep local runtime data inside the repo and avoid polluting your system application-support folders while developing:

```bash
python scripts/run_dev.py
```

That launcher stores local runtime data under:

```text
./app_data_dev_runtime/
```

You can also run the lightweight Qt smoke test on macOS:

```bash
python scripts/smoke_test_qt.py
```

This is useful for quickly validating that the PySide6 app can start on your machine before doing deeper testing.

## OCR Notes

OCR is optional and adds setup complexity.

- Tesseract must be installed separately.
- `pdf2image` may require Poppler, depending on the final OCR path used.
- Version 1 should work without OCR if dependencies are unavailable.

## Field Configuration

Default field definitions live in `config/default_fields.yaml`.

Each field can define:

- `key`
- `display_name`
- `csv_column`
- `type`
- `required`
- `labels`
- `regex_patterns`
- cleanup rules
- confidence rules

Version 1 does not include an in-app field editor. Field changes happen in config files.

## Data Storage on Windows

The app is intended to store runtime data in:

```text
%APPDATA%/BiodataParser/
```

Expected contents:

```text
BiodataParser/
├─ app.db
├─ config/
├─ uploads/
├─ logs/
└─ exports/
```

This keeps data outside the install directory so reinstalls and updates preserve records.

## Data Storage During macOS Development

For local development on macOS, the helper scripts use:

```text
./app_data_dev_runtime/
```

This keeps test data isolated from packaged-app behavior and makes it easy to wipe and retry during development.

## Privacy

- No AI APIs
- No telemetry
- No analytics
- No cloud storage
- No biodata uploads

The only expected network use in later versions is checking GitHub Releases and downloading a released installer.

## CSV Export

CSV export should follow the configured field order and include record metadata such as source filename, review status, and overall confidence.

## Packaging

The Windows app should be packaged with PyInstaller from a Windows environment, ideally through GitHub Actions.

Typical packaging command later:

```bash
pyinstaller app.py --name BiodataParser --windowed
```

## GitHub Actions and Releases

Planned workflow:

- run tests on push and pull request
- build Windows artifacts on tagged releases
- upload installers or packaged artifacts to GitHub Releases

## Release Process

Planned high-level release flow:

1. Merge stable work from `develop` into `main`.
2. Bump the version.
3. Create a version tag.
4. Let GitHub Actions build the Windows artifact.
5. Publish the artifact to GitHub Releases.
6. Test the release on a Windows laptop.

## Windows Install and Test Flow

1. Download the latest installer or artifact from GitHub Releases.
2. Install on a Windows 11 machine.
3. Launch the app and verify `%APPDATA%/BiodataParser/` is created.
4. Import PDFs, review records, view the source PDF, export CSV, and test updates.

## Limitations

- Windows is the only v1 runtime target.
- OCR is optional and may be unavailable locally.
- Parsing accuracy depends on the configured labels and deterministic rules.
- Complex installers and seamless auto-updates are intentionally deferred.
