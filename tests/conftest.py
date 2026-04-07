import pytest
import json
import os
import tempfile
from pathlib import Path
from PIL import Image


@pytest.fixture
def sample_text_message():
    """A plain text message from ZAPiXWEB JSON."""
    return {
        "id": {
            "fromMe": False,
            "remote": "15553332211@c.us",
            "id": "3EB0A12F5060EAF01",
            "_serialized": "false_15553332211@c.us_3EB0A12F5060EAF01"
        },
        "type": "chat",
        "body": "Hello, this is a text message",
        "t": 1684454400,
        "from": "15553332211@c.us",
        "to": "15551112233@c.us",
        "isMedia": False,
    }


@pytest.fixture
def sample_image_message():
    """An image message from ZAPiXWEB JSON."""
    return {
        "id": {
            "fromMe": True,
            "remote": "15553332211@c.us",
            "id": "3EB0B34C7890DEF02",
            "_serialized": "true_15553332211@c.us_3EB0B34C7890DEF02"
        },
        "type": "image",
        "body": "",
        "t": 1684454500,
        "from": "15551112233@c.us",
        "to": "15553332211@c.us",
        "isMedia": True,
        "mimetype": "image/jpeg",
        "mediaData": {"foo": "bar"},
    }


@pytest.fixture
def sample_video_message():
    """A video message from ZAPiXWEB JSON."""
    return {
        "id": {
            "fromMe": False,
            "remote": "15553332211@c.us",
            "id": "3EB0C56D1234ABC03",
            "_serialized": "false_15553332211@c.us_3EB0C56D1234ABC03"
        },
        "type": "video",
        "body": "",
        "t": 1684454600,
        "from": "15553332211@c.us",
        "to": "15551112233@c.us",
        "isMedia": True,
        "mimetype": "video/mp4",
        "mediaData": {"foo": "bar"},
    }


@pytest.fixture
def sample_sticker_message():
    """A sticker message from ZAPiXWEB JSON."""
    return {
        "id": {
            "fromMe": False,
            "remote": "15553332211@c.us",
            "id": "3EB0D78E5678GHI04",
            "_serialized": "false_15553332211@c.us_3EB0D78E5678GHI04"
        },
        "type": "sticker",
        "body": "",
        "t": 1684454700,
        "from": "15553332211@c.us",
        "to": "15551112233@c.us",
        "isMedia": True,
        "mimetype": "image/webp",
        "mediaData": {"foo": "bar"},
    }


@pytest.fixture
def sample_document_message():
    """A document message from ZAPiXWEB JSON."""
    return {
        "id": {
            "fromMe": True,
            "remote": "15553332211@c.us",
            "id": "3EB0E90F9012JKL05",
            "_serialized": "true_15553332211@c.us_3EB0E90F9012JKL05"
        },
        "type": "document",
        "body": "report.pdf",
        "t": 1684454800,
        "from": "15551112233@c.us",
        "to": "15553332211@c.us",
        "isMedia": True,
        "mimetype": "application/pdf",
        "mediaData": {"foo": "bar"},
    }


@pytest.fixture
def sample_audio_message():
    """A push-to-talk audio message from ZAPiXWEB JSON."""
    return {
        "id": {
            "fromMe": False,
            "remote": "15553332211@c.us",
            "id": "3EB0FA103456MNO06",
            "_serialized": "false_15553332211@c.us_3EB0FA103456MNO06"
        },
        "type": "ptt",
        "body": "",
        "t": 1684454900,
        "from": "15553332211@c.us",
        "to": "15551112233@c.us",
        "isMedia": True,
        "mimetype": "audio/ogg; codecs=opus",
        "mediaData": {"foo": "bar"},
    }


@pytest.fixture
def sample_forwarded_message():
    """A forwarded text message from ZAPiXWEB JSON."""
    return {
        "id": {
            "fromMe": False,
            "remote": "15553332211@c.us",
            "id": "3EB0FB204567PQR07",
            "_serialized": "false_15553332211@c.us_3EB0FB204567PQR07"
        },
        "type": "chat",
        "body": "Check out this deal!",
        "t": 1684455000,
        "from": "15553332211@c.us",
        "to": "15551112233@c.us",
        "isMedia": False,
        "isForwarded": True,
    }


@pytest.fixture
def sample_json_conversation(
    sample_text_message, sample_image_message, sample_video_message,
    sample_sticker_message, sample_document_message, sample_audio_message,
    sample_forwarded_message
):
    """A full conversation JSON containing mixed message types."""
    return [
        sample_text_message,
        sample_image_message,
        sample_video_message,
        sample_sticker_message,
        sample_document_message,
        sample_audio_message,
        sample_forwarded_message,
    ]


@pytest.fixture
def json_export_dir(sample_json_conversation):
    """Create a temporary directory mimicking a ZAPiXWEB export with JSON and attachment files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write the conversation JSON
        json_path = os.path.join(tmpdir, "Chat 15553332211@c.us.json")
        with open(json_path, 'w') as f:
            json.dump(sample_json_conversation, f)

        # Create dummy attachment files matching ZAPiXWEB naming
        # Image attachment (fromMe=true)
        img_path = os.path.join(tmpdir, "Attachment true_15553332211@c.us_3EB0B34C7890DEF02.jpeg")
        img = Image.new('RGB', (100, 80), color='red')
        img.save(img_path, 'JPEG')

        # Video attachment (fromMe=false, just a placeholder file)
        video_path = os.path.join(tmpdir, "Attachment false_15553332211@c.us_3EB0C56D1234ABC03.mp4")
        with open(video_path, 'wb') as f:
            f.write(b'\x00' * 100)

        # Sticker attachment (fromMe=false)
        sticker_path = os.path.join(tmpdir, "Attachment false_15553332211@c.us_3EB0D78E5678GHI04.webp")
        img = Image.new('RGBA', (64, 64), color='green')
        img.save(sticker_path, 'WEBP')

        # Document attachment (fromMe=true)
        doc_path = os.path.join(tmpdir, "Attachment true_15553332211@c.us_3EB0E90F9012JKL05.pdf")
        with open(doc_path, 'wb') as f:
            f.write(b'%PDF-1.4 fake')

        # Audio attachment (fromMe=false)
        audio_path = os.path.join(tmpdir, "Attachment false_15553332211@c.us_3EB0FA103456MNO06.ogg")
        with open(audio_path, 'wb') as f:
            f.write(b'\x00' * 50)

        yield tmpdir, json_path


@pytest.fixture
def create_test_image():
    """Create a temporary test image and return its path."""
    def _create(directory, filename="test.jpeg", size=(200, 150), color='blue'):
        path = os.path.join(directory, filename)
        img = Image.new('RGB', size, color=color)
        img.save(path)
        return path
    return _create
