"""Tests for formatter media output (PDF image embedding, CSV/ASCII paths)."""
import csv
import os
import tempfile

import pandas as pd
import pytest
from PIL import Image

from exporter.message_dto import MessageDTO
from utils.formatter import export_to_csv, export_to_pdf, export_to_ascii


def _build_dataframe(messages):
    """Convert MessageDTO list to DataFrame matching exporter.py logic."""
    data = [{
        'message_id': msg.message_id,
        'message_date': msg.message_date,
        'sender_nickname': msg.sender_nickname,
        'receiver_nickname': msg.receiver_nickname,
        'sender_number': msg.sender_number,
        'receiver_number': msg.receiver_number,
        'message_text': msg.message_text,
        'message_direction': msg.message_direction,
        'media_type': msg.media_type,
        'media_path': msg.media_path,
        'is_forwarded': msg.is_forwarded,
    } for msg in messages]
    return pd.DataFrame(data)


@pytest.fixture
def media_messages_with_files():
    """Create MessageDTOs and real attachment files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a real JPEG image
        img_filename = "Attachment IMG001.embedded.jpeg"
        img_path = os.path.join(tmpdir, img_filename)
        img = Image.new('RGB', (200, 150), color='red')
        img.save(img_path, 'JPEG')

        # Create a real PNG image (sticker)
        sticker_filename = "Attachment STK001.embedded.webp"
        sticker_path = os.path.join(tmpdir, sticker_filename)
        img2 = Image.new('RGBA', (64, 64), color='green')
        img2.save(sticker_path, 'WEBP')

        # Create a non-image file (video)
        video_filename = "Attachment VID001.embedded.mp4"
        video_path = os.path.join(tmpdir, video_filename)
        with open(video_path, 'wb') as f:
            f.write(b'\x00' * 100)

        messages = [
            MessageDTO(
                message_id="TXT001",
                message_date="2023-05-19 12:00:00",
                sender_nickname="Alice",
                receiver_nickname="Bob",
                sender_number="15551112233",
                receiver_number="15553332211",
                message_text="Hello!",
                message_direction="OUT",
            ),
            MessageDTO(
                message_id="IMG001",
                message_date="2023-05-19 12:01:00",
                sender_nickname="Bob",
                receiver_nickname="Alice",
                sender_number="15553332211",
                receiver_number="15551112233",
                message_text="",
                message_direction="IN",
                media_type="image",
                media_path=img_filename,
            ),
            MessageDTO(
                message_id="VID001",
                message_date="2023-05-19 12:02:00",
                sender_nickname="Alice",
                receiver_nickname="Bob",
                sender_number="15551112233",
                receiver_number="15553332211",
                message_text="",
                message_direction="OUT",
                media_type="video",
                media_path=video_filename,
            ),
            MessageDTO(
                message_id="STK001",
                message_date="2023-05-19 12:03:00",
                sender_nickname="Bob",
                receiver_nickname="Alice",
                sender_number="15553332211",
                receiver_number="15551112233",
                message_text="",
                message_direction="IN",
                media_type="sticker",
                media_path=sticker_filename,
            ),
        ]

        df = _build_dataframe(messages)
        yield tmpdir, df, messages


class TestCSVMediaOutput:
    def test_csv_contains_media_columns(self, media_messages_with_files):
        tmpdir, df, _ = media_messages_with_files
        csv_path = os.path.join(tmpdir, "output.csv")
        export_to_csv(df, csv_path)

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert 'media_type' in rows[0]
        assert 'media_path' in rows[0]

    def test_csv_text_message_has_empty_media(self, media_messages_with_files):
        tmpdir, df, _ = media_messages_with_files
        csv_path = os.path.join(tmpdir, "output.csv")
        export_to_csv(df, csv_path)

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        text_row = rows[0]
        assert text_row['media_type'] == ''
        assert text_row['media_path'] == ''

    def test_csv_image_message_has_media_path(self, media_messages_with_files):
        tmpdir, df, _ = media_messages_with_files
        csv_path = os.path.join(tmpdir, "output.csv")
        export_to_csv(df, csv_path)

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        img_row = rows[1]
        assert img_row['media_type'] == 'image'
        assert img_row['media_path'] == 'Attachment IMG001.embedded.jpeg'

    def test_csv_video_message_has_media_path(self, media_messages_with_files):
        tmpdir, df, _ = media_messages_with_files
        csv_path = os.path.join(tmpdir, "output.csv")
        export_to_csv(df, csv_path)

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        vid_row = rows[2]
        assert vid_row['media_type'] == 'video'
        assert vid_row['media_path'] == 'Attachment VID001.embedded.mp4'


class TestASCIIMediaOutput:
    def test_ascii_includes_media_path(self, media_messages_with_files, capsys):
        tmpdir, df, _ = media_messages_with_files
        export_to_ascii(df)
        output = capsys.readouterr().out
        assert 'Attachment IMG001.embedded.jpeg' in output
        assert 'Attachment VID001.embedded.mp4' in output


class TestPDFMediaOutput:
    def test_pdf_created_with_media_messages(self, media_messages_with_files):
        tmpdir, df, _ = media_messages_with_files
        pdf_path = os.path.join(tmpdir, "output.pdf")
        export_to_pdf(df, pdf_path, format='json', media_base_dir=tmpdir)
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 0

    def test_pdf_larger_with_embedded_image(self, media_messages_with_files):
        """PDF with embedded images should be larger than one without."""
        tmpdir, df, _ = media_messages_with_files

        # PDF with media
        pdf_with = os.path.join(tmpdir, "with_media.pdf")
        export_to_pdf(df, pdf_with, format='json', media_base_dir=tmpdir)

        # PDF without media (text-only rows)
        text_df = df[df['media_type'].isna()].copy()
        pdf_without = os.path.join(tmpdir, "without_media.pdf")
        export_to_pdf(text_df, pdf_without, format='json', media_base_dir=None)

        assert os.path.getsize(pdf_with) > os.path.getsize(pdf_without)

    def test_pdf_handles_missing_attachment_file(self):
        """If the attachment file doesn't exist, PDF should still generate (show placeholder)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            messages = [
                MessageDTO(
                    message_id="MISS01",
                    message_date="2023-05-19 12:00:00",
                    sender_nickname="Alice",
                    receiver_nickname="Bob",
                    sender_number="15551112233",
                    receiver_number="15553332211",
                    message_text="",
                    message_direction="OUT",
                    media_type="image",
                    media_path="Attachment MISS01.embedded.jpeg",
                ),
            ]
            df = _build_dataframe(messages)
            pdf_path = os.path.join(tmpdir, "output.pdf")
            export_to_pdf(df, pdf_path, format='json', media_base_dir=tmpdir)
            assert os.path.exists(pdf_path)

    def test_pdf_handles_non_image_media(self, media_messages_with_files):
        """Non-image media (video, audio, docs) should show path text, not embed."""
        tmpdir, df, _ = media_messages_with_files
        pdf_path = os.path.join(tmpdir, "output.pdf")
        # Should not raise even though video is not an image
        export_to_pdf(df, pdf_path, format='json', media_base_dir=tmpdir)
        assert os.path.exists(pdf_path)

    def test_pdf_without_media_base_dir_shows_paths(self, media_messages_with_files):
        """When no media_base_dir given, media paths appear as text only."""
        tmpdir, df, _ = media_messages_with_files
        pdf_path = os.path.join(tmpdir, "output.pdf")
        export_to_pdf(df, pdf_path, format='json', media_base_dir=None)
        assert os.path.exists(pdf_path)


class TestPDFInlineMedia:
    """Verify media is rendered inline in the message cell, not a separate column."""

    def test_pdf_no_separate_attachment_column(self, media_messages_with_files):
        """The PDF table should have 8 columns, not 9 — no separate Attachment column."""
        from unittest.mock import patch, MagicMock

        tmpdir, df, _ = media_messages_with_files
        pdf_path = os.path.join(tmpdir, "output.pdf")

        captured_elements = []
        original_build = None

        def capture_build(self_doc, elements):
            captured_elements.extend(elements)
            original_build(self_doc, elements)

        from reportlab.platypus import SimpleDocTemplate
        original_build = SimpleDocTemplate.build

        with patch.object(SimpleDocTemplate, 'build', capture_build):
            export_to_pdf(df, pdf_path, format='json', media_base_dir=tmpdir)

        # Find the Table element
        from reportlab.platypus import Table
        tables = [e for e in captured_elements if isinstance(e, Table)]
        assert len(tables) == 1
        table = tables[0]
        # Header row should have 8 columns (no Attachment column)
        header_row = table._cellvalues[0]
        assert len(header_row) == 8
        assert 'Attachment' not in header_row

    def test_pdf_message_cell_contains_image_flowable(self, media_messages_with_files):
        """For image messages, the message_text cell should contain an image flowable."""
        from unittest.mock import patch
        from reportlab.platypus import SimpleDocTemplate, Table
        from reportlab.platypus import Image as RLImage

        tmpdir, df, _ = media_messages_with_files
        pdf_path = os.path.join(tmpdir, "output.pdf")

        captured_elements = []
        original_build = SimpleDocTemplate.build

        def capture_build(self_doc, elements):
            captured_elements.extend(elements)
            original_build(self_doc, elements)

        with patch.object(SimpleDocTemplate, 'build', capture_build):
            export_to_pdf(df, pdf_path, format='json', media_base_dir=tmpdir)

        tables = [e for e in captured_elements if isinstance(e, Table)]
        table = tables[0]
        # Row 2 is the image message (index 0 is header, 1 is text, 2 is image)
        image_row = table._cellvalues[2]
        message_cell = image_row[6]  # message_text is column index 6
        # Cell should be a sequence of flowables containing at least one RLImage
        assert isinstance(message_cell, (list, tuple))
        has_image = any(isinstance(f, RLImage) for f in message_cell)
        assert has_image


class TestForwardedRendering:
    """Verify forwarded messages are visually marked in all output formats."""

    @pytest.fixture
    def forwarded_messages_df(self):
        messages = [
            MessageDTO(
                message_id="FWD01",
                message_date="2023-05-19 12:00:00",
                sender_nickname="Alice",
                receiver_nickname="Bob",
                sender_number="15551112233",
                receiver_number="15553332211",
                message_text="Forwarded content here",
                message_direction="IN",
                is_forwarded=True,
            ),
            MessageDTO(
                message_id="REG01",
                message_date="2023-05-19 12:01:00",
                sender_nickname="Bob",
                receiver_nickname="Alice",
                sender_number="15553332211",
                receiver_number="15551112233",
                message_text="Normal reply",
                message_direction="OUT",
            ),
        ]
        return _build_dataframe(messages)

    def test_csv_contains_is_forwarded_column(self, forwarded_messages_df):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "output.csv")
            export_to_csv(forwarded_messages_df, csv_path)
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            assert 'is_forwarded' in rows[0]
            assert rows[0]['is_forwarded'] == 'True'
            assert rows[1]['is_forwarded'] == 'False'

    def test_ascii_shows_forwarded_flag(self, forwarded_messages_df, capsys):
        export_to_ascii(forwarded_messages_df)
        output = capsys.readouterr().out
        assert 'is_forwarded' in output
        assert 'True' in output

    def test_pdf_forwarded_message_has_label(self, forwarded_messages_df):
        """Forwarded messages should contain a 'Forwarded' label in the message cell."""
        from unittest.mock import patch
        from reportlab.platypus import SimpleDocTemplate, Table, Paragraph

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "output.pdf")

            captured_elements = []
            original_build = SimpleDocTemplate.build

            def capture_build(self_doc, elements):
                captured_elements.extend(elements)
                original_build(self_doc, elements)

            with patch.object(SimpleDocTemplate, 'build', capture_build):
                export_to_pdf(forwarded_messages_df, pdf_path, format='web')

            tables = [e for e in captured_elements if isinstance(e, Table)]
            table = tables[0]
            # Row 1 is the forwarded message (index 0 is header)
            fwd_row = table._cellvalues[1]
            message_cell = fwd_row[6]  # message_text column
            assert isinstance(message_cell, (list, tuple))
            # First element should be the "Forwarded" label paragraph
            label_text = message_cell[0].text
            assert 'Forwarded' in label_text

    def test_pdf_normal_message_no_forwarded_label(self, forwarded_messages_df):
        """Non-forwarded messages should NOT have a 'Forwarded' label."""
        from unittest.mock import patch
        from reportlab.platypus import SimpleDocTemplate, Table, Paragraph

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "output.pdf")

            captured_elements = []
            original_build = SimpleDocTemplate.build

            def capture_build(self_doc, elements):
                captured_elements.extend(elements)
                original_build(self_doc, elements)

            with patch.object(SimpleDocTemplate, 'build', capture_build):
                export_to_pdf(forwarded_messages_df, pdf_path, format='web')

            tables = [e for e in captured_elements if isinstance(e, Table)]
            table = tables[0]
            # Row 2 is the normal message
            normal_row = table._cellvalues[2]
            message_cell = normal_row[6]
            assert isinstance(message_cell, (list, tuple))
            # No flowable should contain "Forwarded"
            for flowable in message_cell:
                if isinstance(flowable, Paragraph):
                    assert 'Forwarded' not in flowable.text


class TestPDFBackwardCompatibility:
    def test_pdf_without_media_columns(self):
        """Existing DataFrames without media columns should still work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            df = pd.DataFrame([{
                'message_id': '0001',
                'message_date': '2023-05-19 12:00:00',
                'sender_nickname': 'A',
                'receiver_nickname': 'B',
                'sender_number': '1',
                'receiver_number': '2',
                'message_text': 'hello',
                'message_direction': 'OUT',
            }])
            pdf_path = os.path.join(tmpdir, "output.pdf")
            export_to_pdf(df, pdf_path)
            assert os.path.exists(pdf_path)

    def test_csv_without_media_columns(self):
        """Existing DataFrames without media columns should still work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            df = pd.DataFrame([{
                'message_id': '0001',
                'message_date': '2023-05-19 12:00:00',
                'sender_nickname': 'A',
                'receiver_nickname': 'B',
                'sender_number': '1',
                'receiver_number': '2',
                'message_text': 'hello',
                'message_direction': 'OUT',
            }])
            csv_path = os.path.join(tmpdir, "output.csv")
            export_to_csv(df, csv_path)
            assert os.path.exists(csv_path)
