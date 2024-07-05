# WhatsApp Forensic Exporter

A command-line tool for exporting WhatsApp data from a SQLite database.

## Disclaimer

The project is not affiliated, associated, authorized, endorsed by, or in any way officially connected with the WhatsApp LLC, or any of its subsidiaries or its affiliates. The official WhatsApp LLC website can be found at https://www.whatsapp.com/.

## Supported Platforms

- iOS backups (currently supported)
- Android (planned for the future)

## Installation

1. Clone the repository:

```
git clone https://github.com/fdelorenzi/whatsapp-forensic-exporter.git
```


2. Install the dependencies using Poetry:
```
cd whatsapp-forensic-exporter
```
```
poetry install
```


## Usage

To use the tool, run the following command:

```
poetry run python whatsapp-forensic-exporter.py --start-keyword "hello" --end-keyword "good night" --start-date "2023-05-12 00:00:00" --end-date "2023-05-13 23:59:59" --phone-number "15553332211" --db-path "chatstorage.db" --csv-path "output.csv" --pdf-path "output.pdf" --ascii-table --obfuscate-number
```

Replace the values in the command with your desired settings. The tool will export the data to the specified CSV and PDF files, and also output the data as an ASCII table. The `--obfuscate-number` option will obfuscate the phone number in the output.

The `--start-keyword` and `--end-keyword` options define the range of messages to export based on the text of the messages.
The tool will export all messages that occur between the first occurrence of the `--start-keyword` and the last occurrence of the `--end-keyword`. The keyword search is wilcard based (i.e. `%keyword%`)

You can use `%` as start and end keyword to skip the keyword search.

The `--start-date` and `--end-date` options define the range of messages to export based on the timestamp of the messages. The tool will export all messages that occur between the `--start-date` and `--end-date`. The dates should be specified in UTC format (e.g. `YYYY-MM-DD HH:MM:SS`).

The `--csv-path`, `--pdf-path`, and `--ascii-table` options define the output format of the data. 
The `--csv-path` option specifies the path to the output CSV file, the `--pdf-path` option specifies the path to the output PDF file, and the `--ascii-table` option outputs the data as an ASCII table to the console.

To view the help message, run the script with the `-h` or `--help` option:
The help message will display the available options and their descriptions.


## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## Credits
The SQLite query used in the project is inspired by the following script.

- [WhatsAppSQL chat.sql](https://github.com/jammastergirish/WhatsAppSQL/blob/main/chat.sql)

## License

This project is licensed under the MIT License.