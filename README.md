# WhatsApp Forensic Exporter

A command-line forensic tool for exporting and analysing WhatsApp message data from iOS backups and WhatsApp Web takeouts. Produces filtered, presentation-ready reports in CSV, PDF, and ASCII table formats with media attachment support.

## Disclaimer

This project is not affiliated, associated, authorized, endorsed by, or in any way officially connected with WhatsApp LLC, or any of its subsidiaries or affiliates. The official WhatsApp LLC website can be found at https://www.whatsapp.com/.

## Supported Platforms

| Platform | Source | Status |
|----------|--------|--------|
| iOS | `ChatStorage.db` (SQLite) | Supported |
| WhatsApp Web | [ZAPiXWEB](https://github.com/kraftdenker/ZAPiXWEB) JSON takeout | Supported |
| Android | `msgstore.db` | Planned |

## Features

- Filter messages by keyword range, date range, and phone number
- Export to CSV, PDF (landscape A4), and ASCII table
- Media attachment handling:
  - **PDF**: images and stickers embedded inline; video, audio, and document paths labelled
  - **CSV / ASCII**: `media_type` and `media_path` columns with relative file references
- Phone number obfuscation (`--obfuscate-number`, `--obfuscate-me`)
- Multi-language PDF reports (`--language`: en, es, fr, pt, de, it)
- Forwarded message labels in PDF output
- Filter summary footer in PDF reports
- Read-only database access to preserve forensic integrity

## Requirements

- Python 3.10+
- [Poetry](https://python-poetry.org/) for dependency management

## Installation

```bash
git clone https://github.com/fdelorenzi/whatsapp-forensic-exporter.git
cd whatsapp-forensic-exporter
poetry install
```

## Usage

### iOS (ChatStorage.db)

Export messages from an iOS WhatsApp backup database:

```bash
poetry run python whatsapp-forensic-exporter.py \
  --format ios \
  --db-path ChatStorage.db \
  --phone-number "15553332211" \
  --start-date "2023-05-12 00:00:00" \
  --end-date "2023-05-13 23:59:59" \
  --start-keyword "hello" \
  --end-keyword "good night" \
  --csv-path output.csv \
  --pdf-path output.pdf \
  --ascii-table \
  --obfuscate-number
```

Media attachments referenced in the database (images, videos, audio, documents, stickers) are automatically detected. Place the exported media files alongside the database so that PDF reports can embed images inline.

### WhatsApp Web (ZAPiXWEB)

Export chat data from a [ZAPiXWEB](https://github.com/kraftdenker/ZAPiXWEB) JSON takeout:

```bash
poetry run python whatsapp-forensic-exporter.py \
  --format web \
  --json-path "Chat 15556662211@c.us.json" \
  --phone-number "15556662211" \
  --start-date "2023-05-12 00:00:00" \
  --end-date "2023-05-13 23:59:59" \
  --pdf-path output.pdf
```

Extract the ZAPiXWEB ZIP so that `Attachment *.embedded.*` files are in the same directory as the JSON file. The tool will embed images and stickers directly into the PDF report and reference other media types by file path.

### Options

| Option | Description |
|--------|-------------|
| `--format` | Data source format: `ios`, `web`, or `android` (coming soon) |
| `--db-path` | Path to iOS `ChatStorage.db` SQLite database |
| `--json-path` | Path to ZAPiXWEB JSON conversation file |
| `--phone-number` | Phone number to filter messages (required) |
| `--start-date` | Start of date range (`YYYY-MM-DD HH:MM:SS`, UTC) |
| `--end-date` | End of date range (`YYYY-MM-DD HH:MM:SS`, UTC) |
| `--start-keyword` | First keyword to bound the message range (wildcard: `%`) |
| `--end-keyword` | Last keyword to bound the message range (wildcard: `%`) |
| `--csv-path` | Output CSV file path |
| `--pdf-path` | Output PDF file path |
| `--ascii-table` | Print results as an ASCII table to the console |
| `--media-path` | Base directory for media attachments (overrides auto-detection) |
| `--language` | Report language: `en`, `es`, `fr`, `pt`, `de`, `it` (default: `en`) |
| `--obfuscate-number` | Mask counterpart phone numbers in output (e.g., `15**...11`) |
| `--obfuscate-me` | Additionally mask the subject's own phone number |

Use `-h` or `--help` to display the full help message.

## Running Tests

```bash
poetry install
poetry run pytest tests/ -v
```

## Project Structure

```
whatsapp-forensic-exporter.py    # CLI entry point
exporter/
  exporter.py                    # ForensicExporter orchestrator
  ios_sqlite_handler.py          # iOS ChatStorage.db handler
  conversation_json_handler.py   # ZAPiXWEB JSON handler
  message_dto.py                 # MessageDTO data transfer object
utils/
  formatter.py                   # PDF, CSV, and ASCII export functions
tests/                           # Unit tests (pytest)
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## Credits

- SQLite query inspired by [WhatsAppSQL chat.sql](https://github.com/jammastergirish/WhatsAppSQL/blob/main/chat.sql)
- WhatsApp Web takeout support via [ZAPiXWEB](https://github.com/kraftdenker/ZAPiXWEB)

## License

This project is licensed under the MIT License.
