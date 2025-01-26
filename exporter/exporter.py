from exporter.ios_sqlite_handler import IOSSQLiteHandler
from exporter.conversation_json_handler import ConversationJSONHandler
from utils.formatter import export_to_csv, export_to_pdf, export_to_ascii
import pandas as pd

class ForensicExporter:
    def __init__(self, start_keyword, end_keyword, start_date, end_date, phone_number,
                 format, db_path=None, json_path=None, csv_path=None, pdf_path=None, 
                 ascii_table=False, obfuscate_number=False, version=None):
        self.start_keyword = start_keyword
        self.end_keyword = end_keyword
        self.start_date = start_date
        self.end_date = end_date
        self.phone_number = phone_number
        self.format = format
        self.db_path = db_path
        self.json_path = json_path
        self.csv_path = csv_path
        self.pdf_path = pdf_path
        self.ascii_table = ascii_table
        self.obfuscate_number = obfuscate_number
        self.version = version


    def obfuscate_numbers(self, df):
        df['sender_number'] = df['sender_number'].apply(lambda x: str(int(x))[:2] + '*' * (len(str(int(x))) - 4) + str(int(x))[-2:] if pd.notnull(x) and x != '' else x)
        df['receiver_number'] = df['receiver_number'].apply(lambda x: str(int(x))[:2] + '*' * (len(str(int(x))) - 4) + str(int(x))[-2:] if pd.notnull(x) and x != '' else x)
        return df
    
    def messages_to_dataframe(self, messages):
            data = [{
                'message_id': msg.message_id,
                'message_date': msg.message_date,
                'sender_nickname': msg.sender_nickname,
                'receiver_nickname': msg.receiver_nickname,
                'sender_number': msg.sender_number,
                'receiver_number': msg.receiver_number,
                'message_text': msg.message_text,
                'message_direction': msg.message_direction,
            } for msg in messages]
            
            return pd.DataFrame(data)
        
    def export_data(self):
        messages = None
        format = None
        print("\n"
          "==================================================\n"
          "||                                              ||\n"
          "||        WhatsApp Forensic Data Exporter       ||\n"
          "||                                              ||\n"
          "||                Version: " + self.version + "                ||\n"
          "||                                              ||\n"
          "==================================================\n")

        if self.format == 'ios':
                handler = IOSSQLiteHandler(self.db_path)
                messages = handler.get_data(self.start_keyword, self.end_keyword, self.start_date, self.end_date, self.phone_number)
        elif self.format == 'web':
                handler = ConversationJSONHandler(self.json_path)
                messages = handler.get_data(self.start_keyword, self.end_keyword, self.start_date, self.end_date, self.phone_number)
        elif self.format == 'android':
                raise NotImplementedError("Android format export is coming soon.")
        else:
                raise ValueError(f"Unsupported format: {self.format}")

        if messages is not None:
            df = self.messages_to_dataframe(messages)
            if self.obfuscate_number:
                print(f"Obfuscating phone number.")
                df = self.obfuscate_numbers(df)
            
            if self.csv_path:
                export_to_csv(df, self.csv_path)
                print(f"Export to CSV completed: {self.csv_path}")

            if self.pdf_path:
                export_to_pdf(df, self.pdf_path, format)
                print(f"Export to PDF completed: {self.pdf_path}")

            if self.ascii_table:
                export_to_ascii(df)
