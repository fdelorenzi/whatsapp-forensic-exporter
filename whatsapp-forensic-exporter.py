import argparse
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from tabulate import tabulate
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import inch

def export_data(start_keyword, end_keyword, start_date, end_date, phone_number, db_path, csv_path, pdf_path, ascii_table,obfuscate_number):
    # Convert start and end dates to datetime objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
    end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
    
    # Connect to the SQLite database in read-only mode
    conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)

    # Create a temporary table to store the minimum and maximum Z_PK values based on the keywords and date range
    conn.execute("""
    CREATE TEMPORARY TABLE KeywordRange AS
    SELECT
      (SELECT MIN(Z_PK) FROM ZWAMESSAGE WHERE LOWER(ZTEXT) LIKE ? AND datetime(ZMESSAGEDATE + 978307200, 'unixepoch') >= ? AND datetime(ZMESSAGEDATE + 978307200, 'unixepoch') <= ? AND (REPLACE(REPLACE(ZFROMJID, '@s.whatsapp.net', ''), '@g.us', '') = ? OR REPLACE(REPLACE(ZTOJID, '@s.whatsapp.net', ''), '@g.us', '') = ?)) AS min_pk,
      (SELECT MAX(Z_PK) FROM ZWAMESSAGE WHERE LOWER(ZTEXT) LIKE ? AND datetime(ZMESSAGEDATE + 978307200, 'unixepoch') >= ? AND datetime(ZMESSAGEDATE + 978307200, 'unixepoch') <= ? AND (REPLACE(REPLACE(ZFROMJID, '@s.whatsapp.net', ''), '@g.us', '') = ? OR REPLACE(REPLACE(ZTOJID, '@s.whatsapp.net', ''), '@g.us', '') = ?)) AS max_pk;
    """, (f'%{start_keyword}%', start_date, end_date, phone_number, phone_number, f'%{end_keyword}%', start_date, end_date, phone_number, phone_number))

    # Run the query and store the results in a DataFrame
    query = """
    SELECT
      m.Z_PK,
      datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch') AS message_date,
      COALESCE(pn_from.ZPUSHNAME, m.ZFROMJID) AS sender_nickname,
      COALESCE(pn_to.ZPUSHNAME, m.ZTOJID) AS receiver_nickname,
      CASE
        WHEN m.ZFROMJID LIKE '%@g.us' THEN REPLACE(m.ZFROMJID, '@g.us', ' (Group)')
        ELSE REPLACE(m.ZFROMJID, '@s.whatsapp.net', '')
      END AS sender_number,
      CASE
        WHEN m.ZTOJID LIKE '%@g.us' THEN REPLACE(m.ZTOJID, '@g.us', ' (Group)')
        ELSE REPLACE(m.ZTOJID, '@s.whatsapp.net', '')
      END AS receiver_number,
      m.ZTEXT AS message_text,
      CASE
        WHEN m.ZFROMJID IS NULL THEN 'OUT'
        ELSE 'IN'
      END AS message_direction
    FROM
      ZWAMESSAGE m
      LEFT JOIN ZWAPROFILEPUSHNAME pn_from ON pn_from.ZJID = m.ZFROMJID
      LEFT JOIN ZWAPROFILEPUSHNAME pn_to ON pn_to.ZJID = m.ZTOJID
      INNER JOIN KeywordRange kr ON m.Z_PK BETWEEN kr.min_pk AND kr.max_pk
    WHERE
      datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch') >= ?
      AND datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch') < ?
      AND (REPLACE(REPLACE(m.ZFROMJID, '@s.whatsapp.net', ''), '@g.us', '') = ? OR REPLACE(REPLACE(m.ZTOJID, '@s.whatsapp.net', ''), '@g.us', '') = ?)
    ORDER BY
      message_date ASC;
    """
    df = pd.read_sql_query(query, conn, params=(start_date, end_date, phone_number, phone_number))

    # Close the database connection
    conn.close()

    if obfuscate_number:
        df['sender_number'] = df['sender_number'].apply(lambda x: str(int(x))[:2] + '*' * (len(str(int(x))) - 4) + str(int(x))[-2:] if pd.notnull(x) and x != '' else x)
        df['receiver_number'] = df['receiver_number'].apply(lambda x: str(int(x))[:2] + '*' * (len(str(int(x))) - 4) + str(int(x))[-2:] if pd.notnull(x) and x != '' else x)


    # Export the DataFrame to a CSV file
    if csv_path:
        df.to_csv(csv_path, index=False)

    # Export the DataFrame to a PDF file
    if pdf_path:
        export_to_pdf(df, pdf_path)

    # Export the DataFrame to an ASCII table
    if ascii_table:
        print(tabulate(df, headers='keys', tablefmt='psql'))

def export_to_pdf(df, pdf_path):
    # Create a new PDF document in landscape orientation
    doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter))

    # Set the font and font size
    styles = getSampleStyleSheet()
    style = styles['Normal']
    style.fontName = 'Helvetica'
    style.fontSize = 8

    # Define the column widths and starting positions
    col_widths = [inch * 0.5, inch * 1.5, inch * 1.5, inch * 1.5, inch * 1, inch * 1, inch * 2, inch * 1]

    # Define the header row
    header = ['Z_PK', 'Message Date (UTC)', 'From Name', 'To Name', 'From Number', 'To Number', 'Message Text', ' Direction']

    # Create the data rows
    data = [header]
    for index, row in df.iterrows():
        # Wrap the message text to fit within the column width
        message_text = row['message_text']
        if message_text is None:
            message_text = ''
        p = Paragraph(message_text, style)
        data.append([str(row[col]) if col != 'message_text' else p for col in df.columns])

    # Create the table
    table = Table(data, colWidths=col_widths)

    # Set the table style
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    # Build the document
    elements = []
    elements.append(table)
    doc.build(elements)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WhatsApp Forensic Exporter 1.0.0')
    parser.add_argument('--start-keyword', type=str, required=True, help='Starting keyword')
    parser.add_argument('--end-keyword', type=str, required=True, help='Ending keyword')
    parser.add_argument('--start-date', type=str, required=True, help='Starting date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, required=True, help='Ending date (YYYY-MM-DD)')
    parser.add_argument('--phone-number', type=str, required=True, help='Phone number')
    parser.add_argument('--db-path', type=str, required=True, help='Path to the SQLite database')
    parser.add_argument('--csv-path', type=str, help='Path to the output CSV file')
    parser.add_argument('--pdf-path', type=str, help='Path to the output PDF file')
    parser.add_argument('--ascii-table', action='store_true', help='Output the dataset as an ASCII table')
    parser.add_argument('--obfuscate-number', action='store_true', help='Obfuscate phone number')
    
    args = parser.parse_args()

    export_data(args.start_keyword, args.end_keyword, args.start_date, args.end_date, args.phone_number, args.db_path, args.csv_path, args.pdf_path, args.ascii_table, args.obfuscate_number)
