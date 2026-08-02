"""
Адаптер для MCP-сервера (DIP: абстракция над MCP-сервером)
SRP: отвечает только за взаимодействие с MCP-сервером
Реализация без подпроцесса – прямой вызов функций из obsidian_mcp.py
"""

import os
from pathlib import Path
from typing import List, Dict, Any

# Импортируем функции из нашего MCP-сервера
# Предполагается, что файл obsidian_mcp.py лежит рядом с этим файлом
from obsidian_mcp import (
    list_files_in_vault,
    get_file_contents,
    simple_search,
    append_to_daily_note
)


class MCPAdapter:
    """
    Адаптер для взаимодействия с MCP-сервером через прямой вызов функций.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        # Устанавливаем переменную окружения для obsidian_mcp.py
        os.environ["OBSIDIAN_VAULT_PATH"] = str(self.vault_path)

    def list_files(self) -> List[str]:
        """Возвращает список всех .md файлов в хранилище"""
        return list_files_in_vault()

    def get_file_content(self, filepath: str) -> str:
        """Возвращает содержимое файла"""
        return get_file_contents(filepath)

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Выполняет поиск по содержимому"""
        return simple_search(query)

    def append_to_daily_note(self, content: str) -> bool:
        """Добавляет запись в ежедневную заметку"""
        return append_to_daily_note(content)

    def close(self):
        """Закрытие не требуется, т.к. нет подпроцесса"""
        pass