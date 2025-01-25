import sqlite3
import pandas as pd
from datetime import datetime
from typing import List
from exporter.message_dto import MessageDTO

class IOSSQLiteHandler:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_data(self, start_keyword=None, end_keyword=None, start_date=None, end_date=None, phone_number=None) -> List[MessageDTO]:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(f'file:{self.db_path}?mode=ro', uri=True)

        # Construct the keyword range filter if keywords are provided
        if start_keyword or end_keyword:
            self.create_keyword_range_table(conn, start_keyword, start_date, end_date, phone_number, end_keyword)
            keyword_filter = "INNER JOIN KeywordRange kr ON m.Z_PK BETWEEN kr.min_pk AND kr.max_pk"
        else:
            keyword_filter = ""

        query = f"""
        SELECT
          m.Z_PK,
          datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch') AS message_date,
          COALESCE(pn_from.ZPUSHNAME, m.ZFROMJID) AS sender_nickname,
          COALESCE(pn_to.ZPUSHNAME, m.ZTOJID) AS receiver_nickname,
          CASE
            WHEN m.ZFROMJID LIKE '%@g.us' THEN REPLACE(m.ZFROMJID, '@g.us', ' (Group)')
            ELSE REPLACE(m.ZFROMJID, '@s.whatsapp.net', '')
          END AS sender_number,
          CASE
            WHEN m.ZTOJID LIKE '%@g.us' THEN REPLACE(m.ZTOJID, '@g.us', ' (Group)')
            ELSE REPLACE(m.ZTOJID, '@s.whatsapp.net', '')
          END AS receiver_number,
          CASE
            WHEN m.ZMEDIAITEM IS NOT NULL THEN COALESCE(m.ZTEXT,'') || 'Attachment:' || mi.ZVCARDNAME
            ELSE m.ZTEXT
          END AS message_text,
          CASE
            WHEN m.ZFROMJID IS NULL THEN 'OUT'
            ELSE 'IN'
          END AS message_direction
        FROM
          ZWAMESSAGE m
          LEFT JOIN ZWAPROFILEPUSHNAME pn_from ON pn_from.ZJID = m.ZFROMJID
          LEFT JOIN ZWAPROFILEPUSHNAME pn_to ON pn_to.ZJID = m.ZTOJID
          LEFT JOIN ZWAMEDIAITEM mi ON m.ZMEDIAITEM = mi.Z_PK
          {keyword_filter}
        WHERE
          (? IS NULL OR datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch') >= ?)
          AND (? IS NULL OR datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch') < ?)
          AND (? IS NULL OR REPLACE(REPLACE(m.ZFROMJID, '@s.whatsapp.net', ''), '@g.us', '') = ? OR REPLACE(REPLACE(m.ZTOJID, '@s.whatsapp.net', ''), '@g.us', '') = ?)
        ORDER BY
          message_date ASC;
        """

        df = pd.read_sql_query(query, conn, params=(start_date, start_date, end_date, end_date, phone_number, phone_number, phone_number))
        conn.close()

        message_list = [
            MessageDTO(
                message_id=row['Z_PK'],
                message_date=row['message_date'],
                sender_nickname=row['sender_nickname'],
                receiver_nickname=row['receiver_nickname'],
                sender_number=row['sender_number'],
                receiver_number=row['receiver_number'],
                message_text=row['message_text'],
                message_direction=row['message_direction']
            ) for index, row in df.iterrows()
        ]

        return message_list

    def create_keyword_range_table(self, conn, start_keyword=None, start_date=None, end_date=None, phone_number=None, end_keyword=None):
        conn.execute("""
        CREATE TEMPORARY TABLE KeywordRange AS
        SELECT
          (SELECT MIN(Z_PK) FROM ZWAMESSAGE WHERE (? IS NULL OR LOWER(ZTEXT) LIKE ?) AND (? IS NULL OR datetime(ZMESSAGEDATE + 978307200, 'unixepoch') >= ?) AND (? IS NULL OR datetime(ZMESSAGEDATE + 978307200, 'unixepoch') <= ?) AND (? IS NULL OR REPLACE(REPLACE(ZFROMJID, '@s.whatsapp.net', ''), '@g.us', '') = ? OR REPLACE(REPLACE(ZTOJID, '@s.whatsapp.net', ''), '@g.us', '') = ?)) AS min_pk,
          (SELECT MAX(Z_PK) FROM ZWAMESSAGE WHERE (? IS NULL OR LOWER(ZTEXT) LIKE ?) AND (? IS NULL OR datetime(ZMESSAGEDATE + 978307200, 'unixepoch') >= ?) AND (? IS NULL OR datetime(ZMESSAGEDATE + 978307200, 'unixepoch') <= ?) AND (? IS NULL OR REPLACE(REPLACE(ZFROMJID, '@s.whatsapp.net', ''), '@g.us', '') = ? OR REPLACE(REPLACE(ZTOJID, '@s.whatsapp.net', ''), '@g.us', '') = ?)) AS max_pk;
        """, (
            start_keyword, f'%{start_keyword}%', start_date, start_date, end_date, end_date, phone_number, phone_number,
            end_keyword, f'%{end_keyword}%', start_date, start_date, end_date, end_date, phone_number, phone_number
        ))