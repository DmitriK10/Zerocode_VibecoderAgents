"""
Модуль анализа заметок (SRP: отвечает только за анализ)
"""

import re
from collections import Counter
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime


class NoteAnalyzer:
    """
    Анализатор заметок Obsidian.
    Вычисляет статистику: количество заметок, теги, связи, частоту слов.
    """
    
    def __init__(self, files: List[str], content_getter):
        """
        Args:
            files: список путей к файлам
            content_getter: функция для получения содержимого файла
        """
        self.files = files
        self._get_content = content_getter
        self._notes_cache: Dict[str, str] = {}
    
    def _get_note_content(self, filepath: str) -> str:
        """Получает содержимое заметки с кешированием"""
        if filepath not in self._notes_cache:
            self._notes_cache[filepath] = self._get_content(filepath)
        return self._notes_cache[filepath]
    
    def analyze(self) -> Dict[str, Any]:
        """Выполняет полный анализ хранилища"""
        results = {
            "total_notes": len(self.files),
            "tags": {},
            "links": {},
            "word_frequency": {},
            "daily_notes": [],
            "recent_changes": [],
            "backlinks": {},
        }
        
        all_tags = Counter()
        all_links = Counter()
        all_words = Counter()
        daily_notes = []
        
        for filepath in self.files:
            content = self._get_note_content(filepath)
            
            # Извлекаем теги (#тег)
            tags = re.findall(r'#([\w\-/]+)', content)
            all_tags.update(tags)
            
            # Извлекаем внутренние ссылки [[Заметка]]
            links = re.findall(r'\[\[([^\]]+)\]\]', content)
            all_links.update(links)
            
            # Считаем слова (только русские и английские)
            words = re.findall(r'[a-zA-Zа-яА-ЯёЁ]+', content)
            all_words.update([w.lower() for w in words])
            
            # Ежедневные заметки
            if "Daily" in filepath or "daily" in filepath.lower():
                daily_notes.append(filepath)
        
        results["tags"] = dict(all_tags.most_common(20))
        results["links"] = dict(all_links.most_common(20))
        results["word_frequency"] = dict(all_words.most_common(30))
        results["daily_notes"] = daily_notes
        results["daily_notes_count"] = len(daily_notes)
        
        return results
    
    def find_backlinks(self, target_note: str) -> List[str]:
        """Находит все заметки, которые ссылаются на target_note"""
        backlinks = []
        target = target_note.replace(".md", "")
        
        for filepath in self.files:
            content = self._get_note_content(filepath)
            if f"[[{target}" in content or f"[[{target}]]" in content:
                if filepath != target_note:
                    backlinks.append(filepath)
        
        return backlinks
    
    def get_tags_summary(self) -> Dict[str, int]:
        """Возвращает сводку по тегам"""
        all_tags = Counter()
        for filepath in self.files:
            content = self._get_note_content(filepath)
            tags = re.findall(r'#([\w\-/]+)', content)
            all_tags.update(tags)
        return dict(all_tags)
    
    def get_word_count(self) -> int:
        """Возвращает общее количество слов во всех заметках"""
        total = 0
        for filepath in self.files:
            content = self._get_note_content(filepath)
            words = re.findall(r'[a-zA-Zа-яА-ЯёЁ]+', content)
            total += len(words)
        return total