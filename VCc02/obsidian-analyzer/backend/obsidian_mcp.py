#!/usr/bin/env python3
"""
Obsidian MCP Server (kdorff/obsidian-mcp)
Простой MCP-сервер для чтения, поиска и добавления заметок в Obsidian.
Источник: https://github.com/kdorff/obsidian-mcp
"""

import os
import json
import sys
import glob
import re
from datetime import datetime
from pathlib import Path

# Конфигурация из переменных окружения
VAULT_PATH = os.environ.get("OBSIDIAN_VAULT_PATH", os.path.expanduser("~/ObsidianVault"))
DAILY_NOTES_FOLDER = os.environ.get("DAILY_NOTES_FOLDER", "Daily")
DAILY_NOTE_DATE_FORMAT = os.environ.get("DAILY_NOTE_DATE_FORMAT", "%Y-%m-%d %A")


def list_files_in_vault() -> list:
    """Возвращает список всех .md файлов в хранилище"""
    vault = Path(VAULT_PATH)
    if not vault.exists():
        return []
    return [str(f.relative_to(vault)) for f in vault.rglob("*.md")]


def get_file_contents(filepath: str) -> str:
    """Возвращает содержимое файла"""
    full_path = Path(VAULT_PATH) / filepath
    # Защита от path traversal
    if not str(full_path.resolve()).startswith(str(Path(VAULT_PATH).resolve())):
        raise ValueError("Access denied: path traversal detected")
    if not full_path.exists():
        return ""
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def simple_search(query: str) -> list:
    """Простой поиск по содержимому файлов"""
    results = []
    vault = Path(VAULT_PATH)
    for md_file in vault.rglob("*.md"):
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                if query.lower() in content.lower():
                    results.append({
                        "file": str(md_file.relative_to(vault)),
                        "matches": content.count(query)
                    })
        except Exception:
            continue
    return results


def append_to_daily_note(content: str) -> bool:
    """Добавляет запись в ежедневную заметку"""
    today = datetime.now().strftime(DAILY_NOTE_DATE_FORMAT)
    daily_path = Path(VAULT_PATH) / DAILY_NOTES_FOLDER / f"{today}.md"
    daily_path.parent.mkdir(parents=True, exist_ok=True)
    with open(daily_path, "a", encoding="utf-8") as f:
        f.write(f"\n{content}\n")
    return True


def handle_request(request: dict) -> dict:
    """Обрабатывает входящие JSON-RPC запросы"""
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    try:
        if method == "list_files_in_vault":
            result = list_files_in_vault()
        elif method == "get_file_contents":
            result = get_file_contents(params.get("filepath", ""))
        elif method == "simple_search":
            result = simple_search(params.get("query", ""))
        elif method == "append_to_daily_note":
            result = append_to_daily_note(params.get("content", ""))
        else:
            return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": request_id}

        return {"jsonrpc": "2.0", "result": result, "id": request_id}
    except Exception as e:
        return {"jsonrpc": "2.0", "error": {"code": -32000, "message": str(e)}, "id": request_id}


def main():
    """Главный цикл MCP-сервера (stdio транспорт)"""
    print(f"Obsidian MCP Server started. Vault: {VAULT_PATH}", file=sys.stderr)
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            request = json.loads(line)
            response = handle_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()