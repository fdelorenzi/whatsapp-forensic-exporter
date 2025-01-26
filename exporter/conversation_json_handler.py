import json
from datetime import datetime
from typing import List
from exporter.message_dto import MessageDTO

class ConversationJSONHandler:
    def __init__(self, json_path):
        self.json_path = json_path

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
                message_direction=message_direction
            )
            
            message_list.append(dto)

        return message_list