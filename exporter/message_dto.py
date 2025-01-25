from datetime import datetime

class MessageDTO:
    def __init__(self, message_id, message_date, sender_nickname, receiver_nickname, sender_number, receiver_number, message_text, message_direction):
        self.message_id = message_id
        self.message_date = message_date if isinstance(message_date, datetime) else datetime.strptime(message_date, '%Y-%m-%d %H:%M:%S')
        self.sender_nickname = sender_nickname
        self.receiver_nickname = receiver_nickname
        self.sender_number = sender_number
        self.receiver_number = receiver_number
        self.message_text = message_text
        self.message_direction = message_direction