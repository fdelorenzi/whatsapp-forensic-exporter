import os

from exporter.ios_sqlite_handler import IOSSQLiteHandler
from exporter.conversation_json_handler import ConversationJSONHandler
from utils.formatter import export_to_csv, export_to_pdf, export_to_ascii
import pandas as pd

class ForensicExporter:
    def __init__(self, start_keyword, end_keyword, start_date, end_date, phone_number,
                 format, db_path=None, json_path=None, csv_path=None, pdf_path=None,
                 ascii_table=False, obfuscate_number=False, obfuscate_me=False, version=None, media_path=None, language='en'):
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
        self.obfuscate_me = obfuscate_me
        self.version = version
        self.media_path = media_path
        self.language = language


    @staticmethod
    def _obfuscate(value):
        if pd.isnull(value) or value == '':
            return value
        s = ''.join(c for c in str(value) if c.isdigit())
        if len(s) < 4:
            return value
        return s[:2] + '*' * (len(s) - 4) + s[-2:]

    def _obfuscate_col(self, df, number_col, name_col):
        for i, row in df.iterrows():
            original = row[number_col]
            if pd.notnull(original) and original != '':
                obfuscated = self._obfuscate(original)
                df.at[i, number_col] = obfuscated
                if str(row[name_col]).strip() == str(original).strip():
                    df.at[i, name_col] = obfuscated

    def obfuscate_numbers(self, df):
        # OUT: sender = me, receiver = other party
        # IN:  sender = other party, receiver = me
        out_mask = df['message_direction'] == 'OUT'
        in_mask = df['message_direction'] == 'IN'

        # Obfuscate other party
        other_out = df[out_mask].copy()
        other_in = df[in_mask].copy()
        self._obfuscate_col(other_out, 'receiver_number', 'receiver_nickname')
        self._obfuscate_col(other_in, 'sender_number', 'sender_nickname')

        # Obfuscate me (if requested)
        if self.obfuscate_me:
            self._obfuscate_col(other_out, 'sender_number', 'sender_nickname')
            self._obfuscate_col(other_in, 'receiver_number', 'receiver_nickname')

        df.loc[out_mask] = other_out
        df.loc[in_mask] = other_in
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
                'media_type': msg.media_type,
                'media_path': msg.media_path,
                'is_forwarded': msg.is_forwarded,
            } for msg in messages]

            return pd.DataFrame(data)
        
    def export_data(self):
        messages = None
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

            # Build filter summary for PDF footer
            filters = []
            filters.append(f"--format {self.format}")
            phone_display = self.phone_number
            if self.obfuscate_number or self.obfuscate_me:
                phone_display = self._obfuscate(self.phone_number)
            filters.append(f"--phone-number {phone_display}")
            if self.start_date:
                filters.append(f"--start-date \"{self.start_date}\"")
            if self.end_date:
                filters.append(f"--end-date \"{self.end_date}\"")
            if self.start_keyword:
                filters.append(f"--start-keyword \"{self.start_keyword}\"")
            if self.end_keyword:
                filters.append(f"--end-keyword \"{self.end_keyword}\"")
            if self.obfuscate_number:
                filters.append("--obfuscate-number")
            if self.obfuscate_me:
                filters.append("--obfuscate-me")
            filter_summary = ' '.join(filters)

            if self.csv_path:
                export_to_csv(df, self.csv_path)
                print(f"Export to CSV completed: {self.csv_path}")

            if self.pdf_path:
                if self.media_path:
                    media_base_dir = os.path.abspath(self.media_path)
                elif self.json_path:
                    media_base_dir = os.path.dirname(os.path.abspath(self.json_path))
                elif self.db_path:
                    media_base_dir = os.path.dirname(os.path.abspath(self.db_path))
                else:
                    media_base_dir = None
                export_to_pdf(df, self.pdf_path, self.format, media_base_dir=media_base_dir, language=self.language, filter_summary=filter_summary)
                print(f"Export to PDF completed: {self.pdf_path}")

            if self.ascii_table:
                export_to_ascii(df)
