import sqlite3
import os
import random
from datetime import datetime
from config import Config

class SQLiteBackup:
    def __init__(self):
        self.dbpath = Config.SQLITE_FILE
        self._ensure_db()

    def _ensure_db(self):
        os.makedirs(os.path.dirname(self.dbpath), exist_ok=True)
        conn = sqlite3.connect(self.dbpath)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                summ REAL,
                card_number INTEGER,
                birthday TEXT
            )
        """)
        conn.commit()
        conn.close()
        print(f"🗄️ SQLite БД готова: {self.dbpath}")

    def save_user_data(self, full_name: str, birthday: str) -> bool:
        try:
            bday_obj = datetime.strptime(birthday, "%d.%m.%Y")
            bday_str = bday_obj.strftime("%Y-%m-%d")
            summ = round(random.uniform(100.0, 5000.0), 2)
            card_number = random.randint(1000000000000000, 9999999999999999)

            conn = sqlite3.connect(self.dbpath)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (full_name, summ, card_number, birthday)
                VALUES (?, ?, ?, ?)
            """, (full_name, summ, card_number, bday_str))
            conn.commit()
            conn.close()
            print(f"💾 Данные сохранены в SQLite для {full_name}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения в SQLite: {e}")
            return False