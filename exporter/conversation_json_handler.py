import json
from datetime import datetime
from typing import List, Optional
from exporter.message_dto import MessageDTO

MEDIA_TYPES = {'image', 'video', 'ptt', 'document', 'sticker'}

# ZAPiXWEB mimetype-to-extension mapping
MIMETYPE_EXTENSIONS = {
    "image/jpeg": ".jpeg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/x-msvideo": ".avi",
    "video/3gpp": ".3gp",
    "audio/aac": ".aac",
    "audio/ogg": ".ogg",
    "audio/mpeg": ".mp3",
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/x-vcard": ".vcf",
}

class ConversationJSONHandler:
    def __init__(self, json_path):
        self.json_path = json_path

    @staticmethod
    def _get_extension(mimetype: str) -> str:
        """Map a mimetype to file extension, handling params like 'audio/ogg; codecs=opus'."""
        base_mime = mimetype.split(';')[0].strip()
        return MIMETYPE_EXTENSIONS.get(base_mime, ".bin")

    @staticmethod
    def _build_media_path(item: dict) -> Optional[str]:
        """Construct the ZAPiXWEB attachment filename for a media message."""
        msg_type = item.get('type', '')
        if msg_type not in MEDIA_TYPES:
            return None

        mimetype = item.get('mimetype', '')
        if not mimetype:
            return None

        msg_id = item.get('id', {})
        if isinstance(msg_id, dict):
            from_me = str(msg_id.get('fromMe', False)).lower()
            remote = msg_id.get('remote', '')
            short_id = msg_id.get('id', '')
        else:
            return None

        ext = ConversationJSONHandler._get_extension(mimetype)
        return f"Attachment {from_me}_{remote}_{short_id}{ext}"

    def get_data(self, start_keyword: str = None, end_keyword: str = None, start_date: str = None, end_date: str = None, phone_number: str = None) -> List[MessageDTO]:
        with open(self.json_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)

        start_date_dt = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S') if start_date else None
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S') if end_date else None

        message_list = []
        for item in json_data:
            message_date = datetime.fromtimestamp(item['t'])

            if start_date_dt and message_date < start_date_dt:
                continue
            if end_date_dt and message_date >= end_date_dt:
                continue

            sender_number = item['from'].replace('@c.us', '')
            receiver_number = item['to'].replace('@c.us', '')

            if phone_number and phone_number not in {sender_number, receiver_number}:
                continue

            message_text = item.get('body', '').lower()
            if start_keyword and start_keyword.lower() not in message_text:
                continue
            if end_keyword and end_keyword.lower() not in message_text:
                continue

            message_direction = 'OUT' if item['id']['fromMe'] else 'IN'
            message_text = item.get('body', '')

            msg_type = item.get('type', '')
            media_type = msg_type if msg_type in MEDIA_TYPES else None
            media_path = self._build_media_path(item)

            if item['type'] == 'vcard':
                message_text = 'Attachment: ' + item.get('vcardFormattedName', message_text)

            dto = MessageDTO(
                message_id=item['id'].get('id')[-4:],
                message_date=message_date.strftime('%Y-%m-%d %H:%M:%S'),
                sender_nickname=sender_number,
                receiver_nickname=receiver_number,
                sender_number=sender_number,
                receiver_number=receiver_number,
                message_text=message_text,
                message_direction=message_direction,
                media_type=media_type,
                media_path=media_path,
                is_forwarded=bool(item.get('isForwarded', False)),
            )

            message_list.append(dto)

        return message_list