#!/usr/bin/env python3
"""
Obsidian MCP Server (kdorff/obsidian-mcp)
Простой MCP-сервер для чтения, поиска и добавления заметок в Obsidian.
"""

import os
import json
import sys
import re
from datetime import datetime
from pathlib import Path

VAULT_PATH = os.environ.get("OBSIDIAN_VAULT_PATH", os.path.expanduser("~/ObsidianVault"))

def list_files_in_vault() -> list:
    vault = Path(VAULT_PATH)
    if not vault.exists():
        return []
    return [str(f.relative_to(vault)) for f in vault.rglob("*.md")]

def get_file_contents(filepath: str) -> str:
    full_path = Path(VAULT_PATH) / filepath
    if not str(full_path.resolve()).startswith(str(Path(VAULT_PATH).resolve())):
        raise ValueError("Access denied: path traversal detected")
    if not full_path.exists():
        return ""
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()

def get_file_mtime(filepath: str) -> float:
    """Возвращает время модификации файла в секундах с эпохи"""
    full_path = Path(VAULT_PATH) / filepath
    if full_path.exists():
        return full_path.stat().st_mtime
    return 0.0

def simple_search(query: str) -> list:
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
    today = datetime.now().strftime("%Y-%m-%d")
    daily_path = Path(VAULT_PATH) / "Daily" / f"{today}.md"
    daily_path.parent.mkdir(parents=True, exist_ok=True)
    with open(daily_path, "a", encoding="utf-8") as f:
        f.write(f"\n{content}\n")
    return True