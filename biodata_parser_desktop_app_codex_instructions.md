# Codex Instructions: Windows Biodata PDF Parser Desktop App

## 1. Project Goal

Build a Windows desktop application that allows a user to import biodata PDF files, extract selected fields from each PDF, review/edit the extracted data, store it locally, and export the final table to CSV.

The app is intended for arranged-marriage prospect biodatas. The user may receive biodatas in different PDF formats, layouts, and writing styles. The app must support configurable fields and many possible label variations for the same field.

This app must not use AI, LLMs, OpenAI APIs, cloud AI services, or any external AI extraction service.

The extraction should be based on deterministic parsing, OCR fallback, text normalization, label matching, regex, heuristics, and manual review.

Version 1 should target only a local Windows 11 laptop environment. Do not optimize for macOS or cross-platform packaging in v1 unless it adds no meaningful complexity.

## 2. Recommended Tech Stack

Use this stack unless there is a very strong reason not to:

- Language: Python 3.11+
- Desktop UI: PySide6
- Local database: SQLite
- PDF text extraction: PyMuPDF
- Layout/table fallback: pdfplumber
- OCR fallback: pytesseract + Poppler/pdf2image where needed
- CSV export: Python csv module or pandas
- Packaging: PyInstaller initially for Windows
- Config format: YAML or JSON

The app should be designed cleanly, but version 1 should only aim for Windows 11 support.

Development workflow assumption for this project:

- development may happen on macOS
- Windows release artifacts should be built using GitHub Actions
- final release validation should happen on a separate Windows laptop
- do not rely on macOS-only testing for Windows packaging or installer behavior

## 3. Key Requirement: No AI

Do not use:

- OpenAI API
- ChatGPT API
- Azure OpenAI
- AWS Bedrock
- Google Gemini
- Claude
- local LLMs
- vector embeddings
- semantic search models
- AI OCR/document understanding services

The parser must be rules-based and configurable.

## 4. Core User Flow

The app should allow the user to:

1. Open the desktop app.
2. Import one PDF file.
3. Optionally import a folder of PDFs.
4. App extracts raw text from the PDF.
5. App maps the raw text to configured biodata fields.
6. App displays the extracted values in an editable review screen.
7. User corrects wrong/missing fields manually.
8. User saves the record.
9. Main screen shows all imported records in a table.
10. User exports all reviewed records to CSV.

## 5. Main Screens

### 5.1 Main Window

Main window should include:

- Top action buttons:
  - Import PDF
  - Import Folder
  - Export CSV
  - Check for Updates
  - Settings, optional placeholder
- Main table showing extracted profile records
- Filter controls:
  - All
  - Parsed
  - Needs Review
  - Failed
- Search box for quick search by name, phone, city, education, occupation, etc.

The main table should also provide row-level actions for:

- View PDF
- Open/Edit Record
- Delete Record

Table columns should be generated from the configured fields, not hardcoded wherever possible.

Also include internal columns:

- Source File
- Review Status
- Extraction Confidence
- Created At
- Updated At

### 5.2 Record Review/Edit Screen

When a user opens a record:

- Show extracted fields in editable inputs.
- Show confidence per field if possible.
- Show raw extracted text in a scrollable panel.
- Show source PDF file path/name.
- Allow user to save corrections.
- Allow user to mark record as Reviewed.
- Allow user to re-parse the record.

Manual edits made by the user must override parsed data for saved records.

If the user clicks re-parse on a record that already has manual edits, show a confirmation dialog first. Do not overwrite user-corrected values silently.

### 5.3 Settings / Field Configuration Screen

The app should let the user eventually modify fields. For version 1, field configuration must not be editable in the UI.

Version 1 behavior:

- fields are defined in code/config files only
- the user or developer may edit the config file in the project/app data if needed
- the UI may include a placeholder screen or read-only info, but no field editing workflow

The field configuration should support:

- field key
- display name
- output CSV column name
- data type
- possible labels/synonyms
- regex patterns
- required or optional
- post-processing rules
- confidence rules

## 6. Important Design Principle

Do not assume all PDFs use the same labels.

For example, the same value may appear as:

- Name
- Full Name
- Candidate Name
- Bride Name
- Groom Name
- Personal Name

Date of birth may appear as:

- DOB
- D.O.B.
- Date of Birth
- Birth Date
- Born On
- जन्म तारीख
- Janam Tarikh

The app must be configurable so the user can add/update labels without changing core parsing code.

## 7. Configurable Field System

Create a config file, for example:

```yaml
fields:
  - key: full_name
    display_name: Full Name
    csv_column: Full Name
    type: string
    required: true
    labels:
      - name
      - full name
      - candidate name
      - bride name
      - groom name
      - applicant name
      - profile name
    regex_patterns: []
    cleanup:
      trim: true
      collapse_spaces: true
    confidence:
      label_match: 0.9
      regex_match: 0.8
```

The user will later modify this file to add/remove fields.

Do not hardcode the biodata fields deeply into the extraction engine. The extraction engine should read this config and operate generically.

## 8. Suggested Initial Fields

Include a default `fields.yaml` with commonly useful biodata fields. The user may modify this later.

Suggested fields:

- full_name
- gender
- date_of_birth
- age
- birth_time
- birth_place
- height
- weight
- complexion
- religion
- caste
- sub_caste
- gotra
- manglik_status
- mother_tongue
- education
- occupation
- employer_or_business
- annual_income
- current_city
- native_place
- marital_status
- father_name
- father_occupation
- mother_name
- mother_occupation
- siblings
- family_details
- hobbies
- expectations
- contact_number
- alternate_contact_number
- email
- address

Keep this default schema configurable.

## 9. Extraction Strategy

Use a layered deterministic approach.

### Layer 1: PDF Text Extraction

First try PyMuPDF:

- Extract text page by page.
- Preserve page numbers.
- Try sorted text extraction where appropriate.
- Store raw extracted text.

If PyMuPDF text is too short or low-quality, try pdfplumber:

- Extract text with layout hints.
- Try extracting tables if present.
- Combine text and table cells into normalized lines.

If both fail or text is too short, use OCR fallback.

### Layer 2: OCR Fallback

Only use OCR when required.

Detect likely scanned PDF if:

- extracted text length is below threshold
- pages contain images but almost no text
- no meaningful labels are found

OCR approach:

- Convert PDF pages to images.
- Run Tesseract OCR.
- Store OCR text separately.
- Mark extraction source as `ocr`.

Allow OCR to be disabled in settings because it adds dependency/setup complexity.

### Layer 3: Text Normalization

Normalize text before field extraction.

Implement:

- lowercase matching copy
- original text copy for final values
- Unicode normalization
- remove repeated spaces
- normalize colon variants
- normalize bullets and separators
- normalize line endings
- remove decorative repeated characters
- convert tabs to spaces
- split into lines
- remove empty lines

Handle common separators:

- `:`
- `-`
- `–`
- `—`
- `=`
- `|`

### Layer 4: Label-Based Extraction

For each configured field:

1. Iterate over configured labels/synonyms.
2. Search each normalized line for label patterns.
3. Extract value after separator.
4. If value is blank, check next line.
5. Stop at next known label or strong separator.
6. Save extracted value and confidence.

### Layer 5: Regex-Based Extraction

Use regex patterns from field config for fields like:

- phone
- email
- age
- height
- DOB
- income

Regex extraction should be field-specific and should not override a high-confidence label match unless configured.

### Layer 6: Multi-Line Field Extraction

Some fields may span multiple lines:

- family details
- expectations
- education details
- occupation description
- address

Support config option:

```yaml
multiline: true
max_lines: 5
stop_at_next_label: true
```

### Layer 7: Confidence Scoring

Each field should store confidence.

Suggested confidence values:

- exact label match: 0.90
- synonym label match: 0.85
- regex-only match: 0.70
- inferred from nearby text: 0.60
- missing: 0.00

Overall record confidence can be average of important fields.

Mark record as `Needs Review` if:

- required field is missing
- too many fields are missing
- confidence below threshold
- OCR was used
- conflicting values found

## 10. Handling Unknown Field Names

Since fields could be named anything in the PDF, implement strong configurability.

The field config must allow many synonyms for each field.

Also implement a `known_labels` index generated from all configured labels.

Do not attempt fuzzy NLP or AI matching. However, simple deterministic fuzzy matching can be allowed if implemented carefully, such as Levenshtein similarity for minor OCR mistakes, but keep it optional and conservative.

## 11. Data Validation and Cleanup

Implement validators and normalizers per type.

### string

- trim
- collapse repeated whitespace
- remove trailing separators

### date

- support multiple date formats
- output normalized format, preferably `YYYY-MM-DD`
- keep original value separately if normalization fails

### phone

- support Indian phone numbers
- strip spaces, dashes, parentheses
- preserve country code if present
- validate basic length

### email

- extract valid email pattern
- lowercase

### height

Support formats:

- `5'8"`
- `5 ft 8 in`
- `5 feet 8 inches`
- `172 cm`

### income

Support:

- `10 LPA`
- `10 lakhs`
- `₹10,00,000`
- `1000000`

## 12. Database Design

Use SQLite.

Suggested tables:

### profiles

- id INTEGER PRIMARY KEY
- source_file_name TEXT
- source_file_path TEXT
- extraction_method TEXT
- raw_text TEXT
- parsed_json TEXT
- confidence_json TEXT
- overall_confidence REAL
- review_status TEXT
- created_at TEXT
- updated_at TEXT

Store dynamic parsed fields in `parsed_json` so the field schema can change without requiring database migration every time.

### parse_logs

- id INTEGER PRIMARY KEY
- profile_id INTEGER
- event_type TEXT
- message TEXT
- created_at TEXT

## 13. CSV Export

CSV export must use the current field config order.

For each profile:

- read parsed_json
- output columns based on fields.yaml
- include source_file_name
- include review_status
- include overall_confidence

## 14. File Storage

For local app storage:

Use app data directory instead of project directory.

Suggested directories for Windows 11:

- Windows: `%APPDATA%/BiodataParser/`

Inside app data:

```text
BiodataParser/
├─ app.db
├─ config/
│  └─ fields.yaml
├─ uploads/
│  └─ copied_pdf_files/
├─ logs/
│  └─ app.log
└─ exports/
```

When importing a PDF, copy it into app storage so the app has a stable reference even if the original file is moved.

The app must preserve user data across app updates and normal reinstalls as long as the app data directory is not manually deleted.

## 15. Error Handling

The app must not crash on bad PDFs.

Handle:

- encrypted PDFs
- password-protected PDFs
- scanned PDFs
- corrupt PDFs
- PDFs with no extractable text
- missing OCR dependencies
- unsupported file extensions

Show user-friendly messages.

## 16. Duplicate Handling and Deletion

Do not block or prevent duplicates in version 1.

Allow duplicate records to exist.

Instead of duplicate handling, support record deletion directly from the main table.

Deletion behavior:

- user can delete a row from inside the app
- show a confirmation dialog before deleting
- delete should remove the database record
- delete should also remove the copied PDF from app storage if no other record depends on it
- log the deletion event

## 17. Project Structure

Create this structure:

```text
biodata-parser-desktop/
├─ README.md
├─ .gitignore
├─ requirements.txt
├─ pyproject.toml
├─ app.py
├─ config/
│  └─ default_fields.yaml
├─ .github/
│  └─ workflows/
│     ├─ ci.yml
│     └─ release.yml
├─ biodata_parser/
│  ├─ __init__.py
│  ├─ constants.py
│  ├─ paths.py
│  ├─ logging_config.py
│  ├─ ui/
│  │  ├─ __init__.py
│  │  ├─ main_window.py
│  │  ├─ record_dialog.py
│  │  ├─ settings_dialog.py
│  │  └─ table_model.py
│  ├─ parsing/
│  │  ├─ __init__.py
│  │  ├─ pdf_text_extractor.py
│  │  ├─ ocr_extractor.py
│  │  ├─ text_normalizer.py
│  │  ├─ field_config.py
│  │  ├─ field_extractor.py
│  │  ├─ validators.py
│  │  └─ confidence.py
│  ├─ db/
│  │  ├─ __init__.py
│  │  ├─ database.py
│  │  ├─ migrations.py
│  │  └─ repository.py
│  ├─ services/
│  │  ├─ __init__.py
│  │  ├─ import_service.py
│  │  ├─ export_service.py
│  │  ├─ update_service.py
│  │  └─ pdf_open_service.py
│  └─ utils/
│     ├─ __init__.py
│     ├─ file_hash.py
│     └─ dates.py
└─ tests/
   ├─ test_text_normalizer.py
   ├─ test_field_extractor.py
   └─ test_validators.py
```

## 18. Implementation Details

### 18.1 PDF Extraction Module

`pdf_text_extractor.py` should expose:

```python
def extract_text_from_pdf(file_path: str) -> dict:
    ...
```

### 18.2 Field Extractor

`field_extractor.py` should expose:

```python
def extract_fields(raw_text: str, field_config: list[dict]) -> dict:
    ...
```

### 18.3 Import Service

`import_service.py` should:

1. Validate PDF file.
2. Copy PDF to app storage.
3. Compute file hash.
4. Extract text.
5. Extract fields.
6. Save profile record.
7. Return result to UI.

### 18.4 Export Service

`export_service.py` should:

- load profiles from SQLite
- load current field config
- flatten parsed_json
- export CSV using configured column order

### 18.5 PDF Open Service

`pdf_open_service.py` should:

- locate the copied PDF associated with a selected record
- verify that the file still exists
- open it using the default PDF viewer on Windows
- show a user-friendly error if the file is missing or cannot be opened

## 19. UI Requirements

Use PySide6 widgets.

Main UI should be practical, not fancy.

Recommended layout:

- QMainWindow
- QToolBar or top horizontal button row
- QLineEdit search box
- QComboBox status filter
- QTableView for records
- QStatusBar for messages

The table should support convenient row actions. At minimum:

- double-click row to open edit/review dialog
- button or action to view the source PDF
- button or action to delete the row after confirmation

## 20. Review Status Logic

Possible statuses:

- Parsed
- Needs Review
- Reviewed
- Failed

Default status logic:

- Failed: extraction failed completely
- Needs Review: required fields missing or confidence low
- Parsed: extraction succeeded with acceptable confidence
- Reviewed: user manually confirmed/saved the record

If a user manually edits a record and saves it, the manually saved values become the source of truth unless the user explicitly confirms a later re-parse overwrite flow.

## 21. GitHub-Based Update Flow

Version 1 should include a real `Check for Updates` flow for the Windows app.

Expected behavior:

- app stores current version
- user clicks Check for Updates
- app checks the public GitHub Releases page or GitHub release metadata for the latest version
- app compares the installed version with the latest released version
- if a newer version is available, the app should inform the user and offer to download the Windows installer
- the downloaded installer should come from the GitHub Release assets
- if no update is available, show a clear message

Important constraints:

- do not use `git pull` from inside the app
- do not store user data inside the install directory
- updates and reinstalls must preserve app data in `%APPDATA%/BiodataParser/`
- keep update logic simple and safe

GitHub Actions and GitHub Releases should be the release mechanism for publishing new Windows builds.

## 22. Security and Privacy

Biodatas contain personal data. Keep everything local by default.

Requirements:

- no cloud upload
- no AI API calls
- no telemetry
- no analytics
- local SQLite DB only
- local copied PDFs only
- user-controlled CSV export

The app may call GitHub only for version checking and downloading the new installer from the public release assets. No biodata content should ever be uploaded.

## 23. Testing Requirements

Add unit tests for:

- text normalization
- label matching
- date extraction
- phone extraction
- email extraction
- height parsing
- multiline extraction
- missing required fields
- confidence scoring

## 24. First Version Scope

Version 1 should include:

- import single PDF
- import folder of PDFs
- extract text using PyMuPDF
- fallback to pdfplumber
- optional OCR fallback if dependencies are available
- configurable fields.yaml
- label-based extraction
- regex-based extraction
- local SQLite storage
- main records table
- edit/review dialog
- source PDF viewing from the table
- row deletion with confirmation
- CSV export
- basic logs
- Windows update check via GitHub Releases

Do not overbuild:

- no login
- no server backend
- no cloud sync
- no AI
- no multi-user collaboration
- no in-app field config editor in v1
- no duplicate-prevention workflow in v1

## 25. Acceptance Criteria

The project is successful when:

1. User can open the desktop app.
2. User can import a biodata PDF.
3. User can view the copied source PDF from the selected row.
4. App extracts raw text.
5. App extracts configured fields using rules.
6. App saves the result locally.
7. App shows records in a table.
8. User can edit extracted values.
9. User can mark a record as reviewed.
10. User can delete a record after confirmation.
11. User can export the table to CSV.
12. User can check for app updates from public GitHub Releases.
13. App does not use AI or send biodata data to any external service except GitHub update checking/downloading.

## 26. Development Order

Build in this order:

1. Initialize the GitHub repository structure for the `main` branch.
2. Add `.gitignore`, `README.md`, `pyproject.toml`, requirements, and base project folders.
3. Create the initial baseline commit on `main`.
4. Create and use a `develop` branch for application work.
5. Implement Windows app data paths.
6. Implement SQLite database.
7. Implement config loader for `fields.yaml`.
8. Implement text normalizer.
9. Implement field extractor using sample raw text.
10. Implement PDF extraction.
11. Implement import service.
12. Implement CSV export.
13. Build basic PySide6 main window.
14. Build record edit dialog.
15. Add row actions for view PDF and delete record.
16. Add re-parse confirmation behavior when manual edits exist.
17. Add logs and error messages.
18. Add update check service using GitHub Releases.
19. Add unit tests.
20. Add Windows PyInstaller packaging config.
21. Add GitHub Actions workflows for CI and release builds.
22. Prepare GitHub Release process and installer publishing flow.

## 27. Repository, Branching, and Release Workflow

This project will be hosted in a public GitHub repository.

Expected repository workflow:

- create the initial project structure on `main`
- make the first baseline commit on `main`
- create a `develop` branch from `main`
- do ongoing application development on `develop`
- merge stable work from `develop` into `main` for releases

Include a `.gitignore` suitable for:

- Python
- PySide6
- PyInstaller build artifacts
- virtual environments
- IDE files where appropriate
- test/cache artifacts
- Windows packaging output
- local app data dumps used only for development

Use GitHub Actions for:

- running tests on pushes and pull requests
- building Windows release artifacts
- publishing release assets to GitHub Releases when a version tag is created

The release workflow should assume public GitHub Releases are the source of truth for the latest installer version.

Development and validation workflow for this project:

- write and maintain the codebase on macOS
- use GitHub Actions to run CI and build Windows release artifacts
- download the built installer or release artifact onto a Windows laptop for testing
- validate Windows-specific behavior before considering a release ready

Windows validation should include at minimum:

- app launch
- import PDF
- parse and review record
- open source PDF from the table
- edit and save record
- delete record with confirmation
- export CSV
- check for updates
- confirm data persists across reinstall or upgrade scenarios

## 28. README Requirements

Create a detailed `README.md` for this project.

The README should include:

- project overview
- features
- non-AI design principle
- supported environment: local Windows 11 usage
- tech stack
- project structure overview
- setup instructions for development
- note that development may be done on macOS
- dependency installation instructions
- OCR dependency notes
- how to run the app locally
- how field configuration works
- data storage locations on Windows
- privacy notes
- how CSV export works
- how updates work via GitHub Releases
- packaging instructions with PyInstaller
- GitHub Actions release workflow
- how to create a release
- how to test the Windows build on a separate Windows laptop
- how to install the app on a local Windows laptop
- how updates preserve data
- limitations and future improvements

## 29. Final Notes for Codex

Prioritize correctness, maintainability, and configurability over visual polish.

The most important part is not the UI. The most important part is the configurable extraction engine.

Avoid hardcoding biodata-specific field names inside the parser. Use `fields.yaml` so that the user can change extraction fields later.

Every extracted field should ideally include:

- value
- confidence
- extraction method
- source line/evidence

Always allow manual correction, because real biodata PDFs will vary heavily.

Also ensure the implementation aligns with the Windows-only v1 scope, GitHub-based release/update workflow, and local-data-preservation requirement.

Assume the developer may work on macOS, but Windows release builds and release validation must happen through GitHub Actions plus testing on an actual Windows laptop.
