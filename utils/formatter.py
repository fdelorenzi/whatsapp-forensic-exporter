import os

import pandas as pd
from tabulate import tabulate
from datetime import datetime

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus import Image as RLImage

# Media types whose attachment files can be embedded as images in PDF
_EMBEDDABLE_IMAGE_TYPES = {'image', 'sticker'}

# Supported report languages (ISO 639-1)
SUPPORTED_LANGUAGES = ['en', 'es', 'fr', 'pt', 'de', 'it']

_TRANSLATIONS = {
    'en': {
        'id': 'ID', 'zpk': 'Z_PK', 'message_date': 'Message Date (UTC)',
        'from_name': 'From Name', 'to_name': 'To Name',
        'from_number': 'From Number', 'to_number': 'To Number',
        'message_text': 'Message Text', 'direction': 'Direction',
        'forwarded': '[Forwarded Message]',
        'report_generated': 'Report Generated on',
        'id_note': 'Note: Message IDs are truncated to the last 4 digits.',
        'filters_applied': 'Filters applied',
    },
    'es': {
        'id': 'ID', 'zpk': 'Z_PK', 'message_date': 'Fecha del Mensaje (UTC)',
        'from_name': 'Nombre Remitente', 'to_name': 'Nombre Destinatario',
        'from_number': 'N. Remitente', 'to_number': 'N. Destinatario',
        'message_text': 'Texto del Mensaje', 'direction': 'Sentido',
        'forwarded': '[Mensaje Reenviado]',
        'report_generated': 'Informe generado el',
        'id_note': 'Nota: Los ID de mensaje se truncan a los 4 ultimos digitos.',
        'filters_applied': 'Filtros aplicados',
    },
    'fr': {
        'id': 'ID', 'zpk': 'Z_PK', 'message_date': 'Date du Message (UTC)',
        'from_name': "Nom de l'Exp.", 'to_name': 'Nom du Dest.',
        'from_number': 'N. Expediteur', 'to_number': 'N. Destinataire',
        'message_text': 'Texte du Message', 'direction': 'Direction',
        'forwarded': '[Message Transf.]',
        'report_generated': 'Rapport genere le',
        'id_note': 'Note: Les ID de message sont tronques aux 4 derniers chiffres.',
        'filters_applied': 'Filtres appliques',
    },
    'pt': {
        'id': 'ID', 'zpk': 'Z_PK', 'message_date': 'Data da Mensagem (UTC)',
        'from_name': 'Nome Remetente', 'to_name': 'Nome Destinatario',
        'from_number': 'N. Remetente', 'to_number': 'N. Destinatario',
        'message_text': 'Texto da Mensagem', 'direction': 'Sentido',
        'forwarded': '[Mensagem Encaminhada]',
        'report_generated': 'Relatorio gerado em',
        'id_note': 'Nota: Os IDs das mensagens sao truncados para os 4 ultimos digitos.',
        'filters_applied': 'Filtros aplicados',
    },
    'de': {
        'id': 'ID', 'zpk': 'Z_PK', 'message_date': 'Nachrichtendatum (UTC)',
        'from_name': 'Absendername', 'to_name': 'Empfaengername',
        'from_number': 'Absendernr.', 'to_number': 'Empfaengernr.',
        'message_text': 'Nachrichtentext', 'direction': 'Richtung',
        'forwarded': '[Weitergeleitete Nachricht]',
        'report_generated': 'Bericht erstellt am',
        'id_note': 'Hinweis: Nachrichten-IDs werden auf die letzten 4 Ziffern gekuerzt.',
        'filters_applied': 'Angewandte Filter',
    },
    'it': {
        'id': 'ID', 'zpk': 'Z_PK', 'message_date': 'Data Messaggio (UTC)',
        'from_name': 'Nome Mittente', 'to_name': 'Nome Destinatario',
        'from_number': 'N. Mittente', 'to_number': 'N. Destinatario',
        'message_text': 'Testo del Messaggio', 'direction': 'Direzione',
        'forwarded': '[Messaggio Inoltrato]',
        'report_generated': 'Report generato il',
        'id_note': 'Nota: Gli ID dei messaggi sono troncati alle ultime 4 cifre.',
        'filters_applied': 'Filtri applicati',
    },
}

_ALT_ROW_COLOR = colors.Color(0.95, 0.95, 0.95)


def _try_embed_image(media_path, media_type, media_base_dir, max_width=3*inch - 8):
    """Return a reportlab Image flowable if the file exists and is embeddable, else None."""
    if media_type not in _EMBEDDABLE_IMAGE_TYPES:
        return None
    if not media_base_dir or not media_path:
        return None

    abs_path = os.path.join(media_base_dir, media_path)
    if not os.path.isfile(abs_path):
        return None

    try:
        img = RLImage(abs_path)
        iw, ih = img.drawWidth, img.drawHeight
        if iw > 0 and ih > 0:
            # Always scale width to fill the column, preserving aspect ratio
            ratio = max_width / iw
            img.drawWidth = max_width
            img.drawHeight = ih * ratio
        return img
    except Exception:
        return None


def _build_message_cell(row, style, media_style, forwarded_style, has_media, has_forwarded, media_base_dir, lang='en'):
    """Build the message_text cell content as a list of Flowables.

    Text and media are stacked vertically within the same cell.
    """
    cell = []

    # Forwarded label at the top of the cell
    if has_forwarded and row.get('is_forwarded'):
        cell.append(Paragraph(_TRANSLATIONS[lang]['forwarded'], forwarded_style))
        cell.append(Spacer(1, 2))

    message_text = row['message_text'] if row['message_text'] else ''
    if message_text:
        cell.append(Paragraph(str(message_text), style))

    if has_media:
        media_type = row.get('media_type')
        media_path = row.get('media_path')
        if pd.notna(media_type) and pd.notna(media_path):
            embedded = _try_embed_image(media_path, media_type, media_base_dir)
            if embedded:
                if cell:
                    cell.append(Spacer(1, 4))
                cell.append(embedded)
            else:
                # Non-embeddable media or missing file: show path as italic text
                if cell:
                    cell.append(Spacer(1, 4))
                cell.append(Paragraph(f"<i>[{media_type}] {media_path}</i>", media_style))

    if not cell:
        cell.append(Paragraph('', style))

    return cell


def export_to_pdf(df, pdf_path, format='ios', media_base_dir=None, language='en', filter_summary=None):
    page_width, page_height = landscape(A4)
    margin = 20

    doc = SimpleDocTemplate(pdf_path, pagesize=(page_width, page_height),
                            rightMargin=margin, leftMargin=margin,
                            topMargin=margin, bottomMargin=margin)

    styles = getSampleStyleSheet()
    style = styles['Normal']
    style.fontName = 'Helvetica'
    style.fontSize = 8

    media_style = ParagraphStyle(
        'MediaLabel', parent=style, fontSize=7, textColor=colors.Color(0.4, 0.4, 0.4),
    )

    forwarded_style = ParagraphStyle(
        'ForwardedLabel', parent=style, fontSize=7,
        textColor=colors.Color(0.4, 0.4, 0.4), fontName='Helvetica-Oblique',
    )

    has_media = 'media_type' in df.columns and 'media_path' in df.columns
    has_forwarded = 'is_forwarded' in df.columns

    # 8 columns — message_text is wider to accommodate inline media
    col_widths = [
        inch * 0.5,   # ID
        inch * 1.5,   # Message Date
        inch * 1.2,   # From Name
        inch * 1.2,   # To Name
        inch * 1,     # From Number
        inch * 1,     # To Number
        inch * 3,     # Message Text (+ inline media)
        inch * 0.8,   # Direction
    ]
    t = _TRANSLATIONS[language]
    header = [t['zpk'], t['message_date'], t['from_name'], t['to_name'],
              t['from_number'], t['to_number'], t['message_text'], t['direction']]

    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    base_footnote_text = f"{t['report_generated']} {current_datetime}."

    if format == 'json' or format == 'web':
        header[0] = t['id']
        additional_footnote = f" {t['id_note']}"
    else:
        additional_footnote = ""

    footnote_text = base_footnote_text + additional_footnote
    footnote = Paragraph(footnote_text, style)

    base_cols = ['message_id', 'message_date', 'sender_nickname', 'receiver_nickname',
                 'sender_number', 'receiver_number', 'message_text', 'message_direction']

    data = [header]

    wrap_style = ParagraphStyle(
        'WrapCell', parent=style, wordWrap='CJK',
    )
    wrap_cols = {'sender_nickname', 'receiver_nickname', 'sender_number', 'receiver_number'}

    for _, row in df.iterrows():
        row_data = []
        for col in base_cols:
            if col == 'message_text':
                row_data.append(
                    _build_message_cell(row, style, media_style, forwarded_style, has_media, has_forwarded, media_base_dir, lang=language)
                )
            elif col in wrap_cols:
                row_data.append(Paragraph(str(row[col]) if col in row.index else '', wrap_style))
            else:
                row_data.append(str(row[col]) if col in row.index else '')
        data.append(row_data)

    table = Table(data, colWidths=col_widths)

    style_commands = [
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.25, 0.25, 0.30)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        # Data rows
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        # Grid
        ('GRID', (0, 0), (-1, 0), 1, colors.Color(0.2, 0.2, 0.25)),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.Color(0.2, 0.2, 0.25)),
        ('GRID', (0, 1), (-1, -1), 0.5, colors.Color(0.75, 0.75, 0.75)),
    ]

    # Alternating row shading
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_commands.append(('BACKGROUND', (0, i), (-1, i), _ALT_ROW_COLOR))

    table.setStyle(TableStyle(style_commands))

    elements = [table]
    elements.append(Spacer(1, 12))
    elements.append(footnote)

    if filter_summary:
        filter_style = ParagraphStyle(
            'FilterSummary', parent=style, fontSize=7,
            textColor=colors.Color(0.4, 0.4, 0.4), fontName='Helvetica',
        )
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(f"{t['filters_applied']}: {filter_summary}", filter_style))

    doc.build(elements)


def export_to_csv(df, csv_path):
    df.to_csv(csv_path, index=False)

def export_to_ascii(df):
    print(tabulate(df, headers='keys', tablefmt='psql'))
