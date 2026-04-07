"""Tests for IOSSQLiteHandler media field extraction."""
import os
import sqlite3
import tempfile

import pytest

from exporter.ios_sqlite_handler import IOSSQLiteHandler


# Apple Core Data epoch offset
APPLE_EPOCH_OFFSET = 978307200
# 2023-05-19 12:00:00 UTC as Apple timestamp
APPLE_BASE = 1684584000 - APPLE_EPOCH_OFFSET  # Unix 1684584000 → Apple 706276800


@pytest.fixture
def ios_test_db():
    """Create a temporary SQLite DB mimicking iOS ChatStorage.db schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "ChatStorage.db")
        conn = sqlite3.connect(db_path)

        conn.execute("""
            CREATE TABLE ZWAMESSAGE (
                Z_PK INTEGER PRIMARY KEY,
                ZMESSAGEDATE REAL,
                ZFROMJID TEXT,
                ZTOJID TEXT,
                ZTEXT TEXT,
                ZMEDIAITEM INTEGER,
                ZMESSAGETYPE INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE ZWAMEDIAITEM (
                Z_PK INTEGER PRIMARY KEY,
                ZVCARDNAME TEXT,
                ZMEDIALOCALPATH TEXT,
                ZVCARDSTRING TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE ZWAPROFILEPUSHNAME (
                Z_PK INTEGER PRIMARY KEY,
                ZJID TEXT,
                ZPUSHNAME TEXT
            )
        """)

        # Push names
        conn.execute(
            "INSERT INTO ZWAPROFILEPUSHNAME VALUES (1, '15553332211@s.whatsapp.net', 'Alice')"
        )

        # Media items (Z_PK, ZVCARDNAME, ZMEDIALOCALPATH, ZVCARDSTRING)
        conn.execute(
            "INSERT INTO ZWAMEDIAITEM VALUES (1, 'photo.jpg', 'Message/Media/photo-20230519.jpg', 'image/jpeg')"
        )
        conn.execute(
            "INSERT INTO ZWAMEDIAITEM VALUES (2, 'video.mp4', 'Message/Media/video-20230519.mp4', 'video/mp4')"
        )
        conn.execute(
            "INSERT INTO ZWAMEDIAITEM VALUES (3, 'voice.opus', 'Message/Media/audio-20230519.opus', 'audio/ogg; codecs=opus')"
        )
        conn.execute(
            "INSERT INTO ZWAMEDIAITEM VALUES (4, 'doc.pdf', 'Message/Media/document-20230519.pdf', 'application/pdf')"
        )
        conn.execute(
            "INSERT INTO ZWAMEDIAITEM VALUES (5, 'sticker.webp', 'Message/Media/sticker-20230519.webp', 'image/webp')"
        )
        # Media item with NULL local path
        conn.execute(
            "INSERT INTO ZWAMEDIAITEM VALUES (6, 'pending.jpg', NULL, 'image/jpeg')"
        )

        # Messages: ZMESSAGETYPE values — 0=text, 1=image, 2=video, 3=ptt, 8=document
        # Sticker type is unconfirmed; detected via ZVCARDSTRING MIME fallback
        # Text message (no media)
        conn.execute(
            "INSERT INTO ZWAMESSAGE VALUES (1, ?, '15553332211@s.whatsapp.net', "
            "'15551112233@s.whatsapp.net', 'Hello text', NULL, 0)",
            (APPLE_BASE,),
        )
        # Image (ZMESSAGETYPE=1)
        conn.execute(
            "INSERT INTO ZWAMESSAGE VALUES (2, ?, '15553332211@s.whatsapp.net', "
            "'15551112233@s.whatsapp.net', NULL, 1, 1)",
            (APPLE_BASE + 100,),
        )
        # Video (ZMESSAGETYPE=2, outgoing — ZFROMJID is NULL)
        conn.execute(
            "INSERT INTO ZWAMESSAGE VALUES (3, ?, NULL, "
            "'15553332211@s.whatsapp.net', NULL, 2, 2)",
            (APPLE_BASE + 200,),
        )
        # Audio / PTT (ZMESSAGETYPE=3)
        conn.execute(
            "INSERT INTO ZWAMESSAGE VALUES (4, ?, '15553332211@s.whatsapp.net', "
            "'15551112233@s.whatsapp.net', NULL, 3, 3)",
            (APPLE_BASE + 300,),
        )
        # Document (ZMESSAGETYPE=8)
        conn.execute(
            "INSERT INTO ZWAMESSAGE VALUES (5, ?, NULL, "
            "'15553332211@s.whatsapp.net', 'See attached', 4, 8)",
            (APPLE_BASE + 400,),
        )
        # Sticker — ZMESSAGETYPE=15 (unconfirmed, not in map)
        # should fall back to ZVCARDSTRING='image/webp' → 'sticker'
        conn.execute(
            "INSERT INTO ZWAMESSAGE VALUES (6, ?, '15553332211@s.whatsapp.net', "
            "'15551112233@s.whatsapp.net', NULL, 5, 15)",
            (APPLE_BASE + 500,),
        )
        # Image with NULL media path (media item 6)
        conn.execute(
            "INSERT INTO ZWAMESSAGE VALUES (7, ?, '15553332211@s.whatsapp.net', "
            "'15551112233@s.whatsapp.net', NULL, 6, 1)",
            (APPLE_BASE + 600,),
        )

        conn.commit()
        conn.close()
        yield tmpdir, db_path


class TestIOSMediaMessageParsing:
    """Test that media messages are correctly parsed from iOS ChatStorage.db."""

    def test_text_message_has_no_media(self, ios_test_db):
        tmpdir, db_path = ios_test_db
        handler = IOSSQLiteHandler(db_path)
        messages = handler.get_data(phone_number="15553332211")
        text_msgs = [m for m in messages if m.media_type is None]
        assert any(m.message_text == "Hello text" for m in text_msgs)

    def test_image_message_detected(self, ios_test_db):
        tmpdir, db_path = ios_test_db
        handler = IOSSQLiteHandler(db_path)
        messages = handler.get_data(phone_number="15553332211")
        image_msgs = [m for m in messages if m.media_type == "image" and m.media_path is not None]
        assert len(image_msgs) >= 1
        assert image_msgs[0].media_path == "Message/Media/photo-20230519.jpg"

    def test_video_message_detected(self, ios_test_db):
        tmpdir, db_path = ios_test_db
        handler = IOSSQLiteHandler(db_path)
        messages = handler.get_data(phone_number="15553332211")
        video_msgs = [m for m in messages if m.media_type == "video"]
        assert len(video_msgs) == 1
        assert video_msgs[0].media_path == "Message/Media/video-20230519.mp4"

    def test_audio_message_detected(self, ios_test_db):
        tmpdir, db_path = ios_test_db
        handler = IOSSQLiteHandler(db_path)
        messages = handler.get_data(phone_number="15553332211")
        audio_msgs = [m for m in messages if m.media_type == "ptt"]
        assert len(audio_msgs) == 1
        assert audio_msgs[0].media_path == "Message/Media/audio-20230519.opus"

    def test_document_message_detected(self, ios_test_db):
        tmpdir, db_path = ios_test_db
        handler = IOSSQLiteHandler(db_path)
        messages = handler.get_data(phone_number="15553332211")
        doc_msgs = [m for m in messages if m.media_type == "document"]
        assert len(doc_msgs) == 1
        assert doc_msgs[0].media_path == "Message/Media/document-20230519.pdf"
        assert doc_msgs[0].message_text == "See attached"

    def test_sticker_message_detected(self, ios_test_db):
        tmpdir, db_path = ios_test_db
        handler = IOSSQLiteHandler(db_path)
        messages = handler.get_data(phone_number="15553332211")
        sticker_msgs = [m for m in messages if m.media_type == "sticker"]
        assert len(sticker_msgs) == 1
        assert sticker_msgs[0].media_path == "Message/Media/sticker-20230519.webp"

    def test_all_message_count(self, ios_test_db):
        """All 7 messages should be parsed (1 text + 5 media + 1 media with null path)."""
        tmpdir, db_path = ios_test_db
        handler = IOSSQLiteHandler(db_path)
        messages = handler.get_data(phone_number="15553332211")
        assert len(messages) == 7

    def test_null_media_path_handled(self, ios_test_db):
        """Message with media item but NULL ZMEDIALOCALPATH should have media_type but no media_path."""
        tmpdir, db_path = ios_test_db
        handler = IOSSQLiteHandler(db_path)
        messages = handler.get_data(phone_number="15553332211")
        # Message 7 has media_type=image (type 1) but media_path=None (ZMEDIALOCALPATH is NULL)
        msg7 = [m for m in messages if m.message_id == 7]
        assert len(msg7) == 1
        assert msg7[0].media_type == "image"
        assert msg7[0].media_path is None

    def test_message_text_not_polluted_with_attachment_label(self, ios_test_db):
        """Media messages should have clean message_text, not 'Attachment:filename'."""
        tmpdir, db_path = ios_test_db
        handler = IOSSQLiteHandler(db_path)
        messages = handler.get_data(phone_number="15553332211")
        for msg in messages:
            if msg.media_type is not None:
                # message_text should not contain the old 'Attachment:' concatenation
                if msg.message_text:
                    assert "Attachment:" not in msg.message_text


class TestIOSMediaDateFiltering:
    """Ensure date/keyword filters work with media messages."""

    def test_date_filter_includes_media(self, ios_test_db):
        tmpdir, db_path = ios_test_db
        handler = IOSSQLiteHandler(db_path)
        messages = handler.get_data(
            start_date="2023-05-19 00:00:00",
            end_date="2023-05-20 23:59:59",
            phone_number="15553332211",
        )
        media_msgs = [m for m in messages if m.media_type is not None]
        assert len(media_msgs) >= 5

    def test_date_filter_excludes_all(self, ios_test_db):
        tmpdir, db_path = ios_test_db
        handler = IOSSQLiteHandler(db_path)
        messages = handler.get_data(
            start_date="2020-01-01 00:00:00",
            end_date="2020-01-02 00:00:00",
            phone_number="15553332211",
        )
        assert len(messages) == 0
