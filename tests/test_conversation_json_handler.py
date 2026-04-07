"""Tests for ConversationJSONHandler media parsing."""
import json
import os
import pytest

from exporter.conversation_json_handler import ConversationJSONHandler


class TestMediaMessageParsing:
    """Test that media messages are correctly parsed from ZAPiXWEB JSON."""

    def test_text_message_has_no_media(self, json_export_dir):
        tmpdir, json_path = json_export_dir
        handler = ConversationJSONHandler(json_path)
        messages = handler.get_data(phone_number="15553332211")
        text_msgs = [m for m in messages if m.media_type is None]
        assert len(text_msgs) >= 1
        assert text_msgs[0].message_text == "Hello, this is a text message"

    def test_image_message_detected(self, json_export_dir):
        tmpdir, json_path = json_export_dir
        handler = ConversationJSONHandler(json_path)
        messages = handler.get_data(phone_number="15553332211")
        image_msgs = [m for m in messages if m.media_type == "image"]
        assert len(image_msgs) == 1
        assert image_msgs[0].media_path == "Attachment true_15553332211@c.us_3EB0B34C7890DEF02.jpeg"

    def test_video_message_detected(self, json_export_dir):
        tmpdir, json_path = json_export_dir
        handler = ConversationJSONHandler(json_path)
        messages = handler.get_data(phone_number="15553332211")
        video_msgs = [m for m in messages if m.media_type == "video"]
        assert len(video_msgs) == 1
        assert video_msgs[0].media_path == "Attachment false_15553332211@c.us_3EB0C56D1234ABC03.mp4"

    def test_sticker_message_detected(self, json_export_dir):
        tmpdir, json_path = json_export_dir
        handler = ConversationJSONHandler(json_path)
        messages = handler.get_data(phone_number="15553332211")
        sticker_msgs = [m for m in messages if m.media_type == "sticker"]
        assert len(sticker_msgs) == 1
        assert sticker_msgs[0].media_path == "Attachment false_15553332211@c.us_3EB0D78E5678GHI04.webp"

    def test_document_message_detected(self, json_export_dir):
        tmpdir, json_path = json_export_dir
        handler = ConversationJSONHandler(json_path)
        messages = handler.get_data(phone_number="15553332211")
        doc_msgs = [m for m in messages if m.media_type == "document"]
        assert len(doc_msgs) == 1
        assert doc_msgs[0].media_path == "Attachment true_15553332211@c.us_3EB0E90F9012JKL05.pdf"

    def test_audio_message_detected(self, json_export_dir):
        tmpdir, json_path = json_export_dir
        handler = ConversationJSONHandler(json_path)
        messages = handler.get_data(phone_number="15553332211")
        audio_msgs = [m for m in messages if m.media_type == "ptt"]
        assert len(audio_msgs) == 1
        assert audio_msgs[0].media_path == "Attachment false_15553332211@c.us_3EB0FA103456MNO06.ogg"

    def test_media_path_is_relative_to_json_dir(self, json_export_dir):
        """Media paths should be relative filenames (same dir as JSON), not absolute."""
        tmpdir, json_path = json_export_dir
        handler = ConversationJSONHandler(json_path)
        messages = handler.get_data(phone_number="15553332211")
        for msg in messages:
            if msg.media_path:
                assert not os.path.isabs(msg.media_path)
                assert "/" not in msg.media_path  # flat in same directory

    def test_all_message_count(self, json_export_dir):
        """All 7 messages (1 text + 5 media + 1 forwarded) should be parsed."""
        tmpdir, json_path = json_export_dir
        handler = ConversationJSONHandler(json_path)
        messages = handler.get_data(phone_number="15553332211")
        assert len(messages) == 7

    def test_mimetype_with_params_handled(self, json_export_dir):
        """audio/ogg; codecs=opus should map to .ogg extension."""
        tmpdir, json_path = json_export_dir
        handler = ConversationJSONHandler(json_path)
        messages = handler.get_data(phone_number="15553332211")
        audio_msgs = [m for m in messages if m.media_type == "ptt"]
        assert len(audio_msgs) == 1
        assert audio_msgs[0].media_path.endswith(".ogg")


class TestForwardedMessageParsing:
    """Test that isForwarded field is correctly parsed from ZAPiXWEB JSON."""

    def test_forwarded_message_detected(self, json_export_dir):
        tmpdir, json_path = json_export_dir
        handler = ConversationJSONHandler(json_path)
        messages = handler.get_data(phone_number="15553332211")
        fwd_msgs = [m for m in messages if m.is_forwarded]
        assert len(fwd_msgs) == 1
        assert fwd_msgs[0].message_text == "Check out this deal!"

    def test_non_forwarded_messages_are_false(self, json_export_dir):
        tmpdir, json_path = json_export_dir
        handler = ConversationJSONHandler(json_path)
        messages = handler.get_data(phone_number="15553332211")
        non_fwd = [m for m in messages if not m.is_forwarded]
        assert len(non_fwd) == 6  # all except the forwarded one


class TestMediaMessageDateFiltering:
    """Ensure date/keyword filters still work with media messages."""

    def test_date_filter_includes_media(self, json_export_dir):
        tmpdir, json_path = json_export_dir
        handler = ConversationJSONHandler(json_path)
        # All test messages are around timestamp 1684454400-1684454900 → 2023-05-19
        messages = handler.get_data(
            start_date="2023-05-19 00:00:00",
            end_date="2023-05-20 00:00:00",
            phone_number="15553332211",
        )
        media_msgs = [m for m in messages if m.media_type is not None]
        assert len(media_msgs) == 5

    def test_date_filter_excludes_media(self, json_export_dir):
        tmpdir, json_path = json_export_dir
        handler = ConversationJSONHandler(json_path)
        messages = handler.get_data(
            start_date="2020-01-01 00:00:00",
            end_date="2020-01-02 00:00:00",
            phone_number="15553332211",
        )
        assert len(messages) == 0
