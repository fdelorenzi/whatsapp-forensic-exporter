import argparse
from exporter.exporter import ForensicExporter

VERSION='1.1.0'
APP_NAME = 'WhatsApp Forensic Exporter'

def parse_args():
    parser = argparse.ArgumentParser(
        description=f'{APP_NAME} {VERSION}',
        epilog='Example: python whatsapp-forensic-exporter.py --format ios --db-path messages.db --start-keyword hello --end-keyword bye --start-date \'2023-01-01 00:00:00\' --end-date \'2023-01-31 00:00:00\' --phone-number 441234567890 --ascii-table'
    )

    parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    
    # Create mutually exclusive group for data source selection
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument('--db-path', type=str, help='Path to the SQLite database')
    source_group.add_argument('--json-path', type=str, help='Path to the JSON file')

   # Add argument for specifying the format of the data, defaulting to ios
    parser.add_argument('--format', type=str, choices=['ios', 'android', 'web'], default='ios',
                        help='Data format: ios (ChatStorage.db) [default], android (msgstore.db - coming soon), web (Zapixweb compatible JSON)')

    # Required keyword and date arguments
    parser.add_argument('--start-keyword', type=str, required=False, help='Starting keyword for message filtering')
    parser.add_argument('--end-keyword', type=str, required=False, help='Ending keyword for message filtering')
    parser.add_argument('--start-date', type=str, required=False, help='Starting date (format YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--end-date', type=str, required=False, help='Ending date (format YYYY-MM-DD HH:MM:SS)')

    # Phone number, required for filtering
    parser.add_argument('--phone-number', type=str, required=True, help='Phone number to filter messages')

    # Output options
    output_group = parser.add_argument_group('Output options')
    output_group.add_argument('--csv-path', type=str, help='Path to save the output as a CSV file')
    output_group.add_argument('--pdf-path', type=str, help='Path to save the output as a PDF file')
    output_group.add_argument('--ascii-table', action='store_true', help='Print the dataset as an ASCII table')

    # Optional argument for obfuscation
    parser.add_argument('--obfuscate-number', action='store_true', help='Obfuscate phone numbers in the output')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    # Validate the format and path combinations
    if args.json_path and args.format not in ['web']:
        raise ValueError("When using --json-path, --format must be set to web.")
    
    # Instantiate ForensicExporter with parsed arguments
    exporter = ForensicExporter(
        start_keyword=args.start_keyword,
        end_keyword=args.end_keyword,
        start_date=args.start_date,
        end_date=args.end_date,
        phone_number=args.phone_number,
        format=args.format,
        db_path=args.db_path,
        json_path=args.json_path,
        csv_path=args.csv_path,
        pdf_path=args.pdf_path,
        ascii_table=args.ascii_table,
        obfuscate_number=args.obfuscate_number,
        version=VERSION
    )

    # Execute data export
    exporter.export_data()