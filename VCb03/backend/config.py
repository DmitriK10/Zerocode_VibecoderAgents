# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # YandexGPT
    YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
    YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
    YANDEX_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    YANDEX_MODEL = "yandexgpt-lite"
    YANDEX_TIMEOUT = 60

    # ProxyAPI
    PROXY_API_KEY = os.getenv('PROXY_API_KEY')
    PROXY_BASE_URL = os.getenv('PROXY_BASE_URL', 'https://api.proxyapi.ru/openai/v1')
    PROXY_MODEL = os.getenv('PROXY_MODEL', 'gpt-4o-mini')
    PROXY_TIMEOUT = 60

    # Server
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'pdf'}
    ALLOWED_MIMETYPES = {
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xls': 'application/vnd.ms-excel',
        'csv': 'text/csv',
        'pdf': 'application/pdf'
    }
    UPLOAD_FOLDER = 'uploads'