import pandas as pd
from tabulate import tabulate
from datetime import datetime

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

def export_to_pdf(df, pdf_path,format='ios'):
    page_width, page_height = landscape(A4)
    margin = 20

    doc = SimpleDocTemplate(pdf_path, pagesize=(page_width, page_height), 
                            rightMargin=margin, leftMargin=margin,
                            topMargin=margin, bottomMargin=margin)

    styles = getSampleStyleSheet()
    style = styles['Normal']
    style.fontName = 'Helvetica'
    style.fontSize = 8  # Small font to fit more text

    col_widths = [inch * 0.5, inch * 1.5, inch * 1.5, inch * 1.5, inch * 1, inch * 1, inch * 2, inch * 1]
    header = ['Z_PK', 'Message Date (UTC)', 'From Name', 'To Name', 'From Number', 'To Number', 'Message Text', 'Direction']

    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    base_footnote_text = f"Report Generated on {current_datetime}."

    if format == 'json':
        header[0] = 'ID'
        additional_footnote = " Note: Message IDs are truncated to the last 4 digits."
    else:
        additional_footnote = ""

    footnote_text = base_footnote_text + additional_footnote
    footnote = Paragraph(footnote_text, style)

    data = [header]

    # Function to split long text into smaller parts
    def split_text(message_text, max_length=120):
        return [Paragraph(message_text[i:i+max_length], style) for i in range(0, len(message_text), max_length)]

    for index, row in df.iterrows():
        message_text = row['message_text'] if row['message_text'] else ''
        text_paragraphs = split_text(message_text) if len(message_text) > 300 else [Paragraph(message_text, style)]
        
        # Add the first part with all other column details
        row_data = [str(row[col]) if col != 'message_text' else text_paragraphs[0] for col in df.columns]
        data.append(row_data)
        
        # Add other text parts as continuation rows
        if len(text_paragraphs) > 1:
            continuation_marker = "..."
            for text_part in text_paragraphs[1:]:
                continuation_data = [continuation_marker if col != 'message_text' else text_part for col in df.columns]
                data.append(continuation_data)

    table = Table(data, colWidths=col_widths)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))

    elements = [table]
    
    if format == 'json':
            elements.append(Spacer(1, 12))
            elements.append(footnote)
            
    doc.build(elements)


def export_to_csv(df, csv_path):
    df.to_csv(csv_path, index=False)

def export_to_ascii(df):
    print(tabulate(df, headers='keys', tablefmt='psql'))