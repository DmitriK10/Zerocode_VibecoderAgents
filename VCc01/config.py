import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    EXCEL_FILE = os.getenv("EXCEL_FILE", "backups/users_backup.xlsx")
    SQLITE_FILE = os.getenv("SQLITE_FILE", "backups/users.sqlite")