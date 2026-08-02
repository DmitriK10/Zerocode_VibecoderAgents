"""
Модуль конфигурации (SRP: отвечает только за настройки)
"""

import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()


class Config:
    """Класс-контейнер для конфигурации (DIP: абстракция для настроек)"""
    
    # Путь к хранилищу Obsidian
    OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "/vault")
    
    # Настройки MCP-сервера
    MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "mcp-server")
    MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8080"))
    
    # Настройки OpenAI (с ограничением и прокси)
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-16k")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://proxypi.ru/v1")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-dummy-key")  # <-- ИСПРАВЛЕНО
    
    # Настройки Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_ENV") == "development"


# Создаём экземпляр конфигурации
config = Config()