"""Tests for MessageDTO media field support."""
from exporter.message_dto import MessageDTO


class TestMessageDTOMediaFields:
    def test_text_message_has_no_media(self):
        dto = MessageDTO(
            message_id="1234",
            message_date="2023-05-19 12:00:00",
            sender_nickname="Alice",
            receiver_nickname="Bob",
            sender_number="15551112233",
            receiver_number="15553332211",
            message_text="Hello",
            message_direction="OUT",
        )
        assert dto.media_type is None
        assert dto.media_path is None

    def test_image_message_carries_media_fields(self):
        dto = MessageDTO(
            message_id="5678",
            message_date="2023-05-19 12:01:00",
            sender_nickname="Alice",
            receiver_nickname="Bob",
            sender_number="15551112233",
            receiver_number="15553332211",
            message_text="",
            message_direction="OUT",
            media_type="image",
            media_path="Attachment 5678.embedded.jpeg",
        )
        assert dto.media_type == "image"
        assert dto.media_path == "Attachment 5678.embedded.jpeg"

    def test_video_message_carries_media_fields(self):
        dto = MessageDTO(
            message_id="9012",
            message_date="2023-05-19 12:02:00",
            sender_nickname="Bob",
            receiver_nickname="Alice",
            sender_number="15553332211",
            receiver_number="15551112233",
            message_text="",
            message_direction="IN",
            media_type="video",
            media_path="Attachment 9012.embedded.mp4",
        )
        assert dto.media_type == "video"
        assert dto.media_path == "Attachment 9012.embedded.mp4"

    def test_backward_compatible_without_media_kwargs(self):
        """Existing callers that don't pass media_type/media_path should still work."""
        dto = MessageDTO(
            message_id="0001",
            message_date="2023-05-19 12:00:00",
            sender_nickname="A",
            receiver_nickname="B",
            sender_number="1",
            receiver_number="2",
            message_text="hi",
            message_direction="IN",
        )
        assert dto.media_type is None
        assert dto.media_path is None
