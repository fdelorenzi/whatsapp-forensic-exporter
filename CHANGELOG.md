# Changelog

## [1.2.0] - 2026-04-07

### Added
- Media attachment support for WhatsApp Web (ZAPiXWEB) exports: images, videos, audio, documents, and stickers are now detected and linked from the JSON takeout data.
- Media attachment support for iOS exports: `ZMEDIALOCALPATH` and `ZMESSAGETYPE` are now extracted from `ChatStorage.db`, providing media type classification and file path references.
- PDF image embedding: image and sticker attachments are rendered inline within the Message Text column of PDF reports. Non-image media (video, audio, documents) display a labelled file path reference.
- `media_type` and `media_path` columns in CSV and ASCII table output, referencing attachment files relative to the export directory.
- `--media-path` option to specify a custom base directory for media attachments (overrides auto-detection from `--db-path` or `--json-path`).
- Multi-language PDF report support via `--language` option (en, es, fr, pt, de, it). Column headers, footnotes, and labels are translated.
- Forwarded message indicator: messages marked as forwarded in ZAPiXWEB data display a `[Forwarded Message]` label (localised) in the PDF Message Text cell.
- `--obfuscate-me` flag to additionally obfuscate the subject's own phone number (the number passed via `--phone-number`), complementing the existing `--obfuscate-number` which masks the counterpart.
- Filter summary footer in PDF reports showing the CLI arguments used to generate the export.
- Unit test suite (40 tests) covering media parsing, PDF rendering, CSV/ASCII output, iOS handler, and backward compatibility.
- Pillow dependency for image handling in PDF reports.
- pytest as a dev dependency.

### Changed
- PDF report layout: removed the separate "Attachment" column; media is now embedded inline within the Message Text cell for a cleaner, more readable report.
- PDF styling: darker header, alternating row shading, lighter grid lines, improved cell padding.
- Widened Message Text column from 2" to 3" to accommodate inline media content.
- iOS handler no longer concatenates `Attachment:<filename>` into `message_text`; attachment metadata is now in dedicated `media_type` and `media_path` fields.
- Obfuscation logic improved: now direction-aware (IN/OUT) and also masks nicknames that match the obfuscated number.
- Minimum Python version bumped from 3.8 to 3.10.
- Updated dependency floors for Python 3.13 compatibility (pandas >= 2.1.0, numpy >= 1.26.0, reportlab >= 4.0.0).

### Fixed
- `format` variable in `ForensicExporter.export_data()` was always `None` when passed to `export_to_pdf`, causing the PDF footnote to never render for web/JSON exports.
- `media_base_dir` is now derived from `db_path` for iOS exports (previously only set for JSON exports).

## [1.1.0] - 2025-01-26

### Added
- Support for exporting messages from WhatsApp Web via [ZAPiXWEB](https://github.com/kraftdenker/ZAPiXWEB) JSON takeouts using the `--format web` and `--json-path` options.
- `ConversationJSONHandler` for parsing ZAPiXWEB JSON conversation files.
- `MessageDTO` data transfer object for standardised message representation across handlers.
- `IOSSQLiteHandler` extracted from monolithic script for iOS `ChatStorage.db` queries.
- `utils/formatter.py` module with dedicated `export_to_pdf`, `export_to_csv`, and `export_to_ascii` functions.
- Contact attachment (vCard) export support.

### Changed
- Refactored from a single-file script into a modular package structure (`exporter/`, `utils/`).
- Argument parser now uses a mutually exclusive group for `--db-path` and `--json-path`.

## [1.0.0] - 2024-07-05

### Added
- Initial release.
- Export WhatsApp messages from iOS `ChatStorage.db` SQLite databases.
- Filter messages by keyword range, date range, and phone number.
- Output formats: CSV, PDF (landscape A4 table), and ASCII table.
- Phone number obfuscation with `--obfuscate-number`.
- Read-only database access to preserve forensic integrity.
