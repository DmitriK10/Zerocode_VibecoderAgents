# task_service.py
import asyncio
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Optional

from config import settings
from logger import logger
from runners import run_ai_history, run_seo_analysis, run_custom_task


class TaskService:
    """Сервис для управления выполнением задач, кэшированием и отменой."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._cache_dir = Path(__file__).parent / ".cache"
        self._cache_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Возвращает путь к файлу кэша для ключа."""
        hashed = hashlib.md5(key.encode()).hexdigest()
        return self._cache_dir / f"{hashed}.json"

    def _get_cached_result(self, key: str) -> Optional[str]:
        """Возвращает закэшированный результат, если он актуален."""
        cache_path = self._get_cache_path(key)   # ИСПРАВЛЕНО: было self._cache_path
        if not cache_path.exists():
            return None
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if time.time() - data["timestamp"] > settings.seo_cache_ttl:
                return None
            return data["result"]
        except Exception:
            return None

    def _save_cache(self, key: str, result: str) -> None:
        """Сохраняет результат в кэш."""
        cache_path = self._get_cache_path(key)   # ИСПРАВЛЕНО: было self._cache_path
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump({"timestamp": time.time(), "result": result}, f)
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша: {e}")

    def generate_task_id(self, task_type: str, *args, **kwargs) -> str:
        """Публичный метод для генерации ID задачи (используется для отмены)."""
        key = f"{task_type}:{args}:{kwargs}"
        return hashlib.md5(key.encode()).hexdigest()

    async def run_task(
        self,
        task_type: str,
        *args,
        use_cache: bool = True,
        **kwargs
    ) -> str:
        """
        Запускает задачу с учётом кэширования.
        Поддерживаемые task_type: 'ai_history', 'seo', 'custom'.
        """
        task_id = self.generate_task_id(task_type, *args, **kwargs)

        # Проверка кэша
        if use_cache and task_type == "seo":
            cache_key = f"seo:{args[0]}"  # URL
            cached = self._get_cached_result(cache_key)
            if cached is not None:
                logger.info(f"Возврат закэшированного SEO-результата для {args[0]}")
                return cached

        # Проверка, не выполняется ли уже такая задача
        if task_id in self._active_tasks:
            logger.warning(f"Задача {task_id} уже выполняется, ожидание...")
            try:
                result = await self._active_tasks[task_id]
                return result
            except Exception as e:
                logger.error(f"Ошибка выполнения задачи {task_id}: {e}")
                raise

        # Запуск задачи
        loop = asyncio.get_running_loop()
        if task_type == "ai_history":
            enable_fact_check = args[0] if args else False
            future = loop.run_in_executor(None, run_ai_history, enable_fact_check)
        elif task_type == "seo":
            url = args[0]
            future = loop.run_in_executor(None, run_seo_analysis, url)
        elif task_type == "custom":
            query = args[0]
            if len(query) > settings.max_custom_query_length:
                raise ValueError(f"Запрос превышает максимальную длину {settings.max_custom_query_length}")
            future = loop.run_in_executor(None, run_custom_task, query)
        else:
            raise ValueError(f"Неизвестный тип задачи: {task_type}")

        # Сохраняем задачу
        task = asyncio.create_task(self._wrap_future(future, task_id))
        self._active_tasks[task_id] = task

        try:
            result = await task
            # Сохраняем в кэш для SEO
            if use_cache and task_type == "seo":
                cache_key = f"seo:{args[0]}"
                self._save_cache(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"Ошибка выполнения задачи {task_id}: {e}")
            raise
        finally:
            self._active_tasks.pop(task_id, None)

    async def _wrap_future(self, future, task_id: str) -> str:
        """Обёртка для обработки исключений."""
        try:
            return await future
        except Exception as e:
            logger.error(f"Задача {task_id} завершилась с ошибкой: {e}")
            raise

    def cancel_task(self, task_id: str) -> bool:
        """Отменяет выполнение задачи по ID."""
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            if not task.done():
                task.cancel()
                logger.info(f"Задача {task_id} отменена")
                return True
        return False

    def get_active_tasks(self) -> Dict[str, str]:
        """Возвращает список активных задач (ID -> статус)."""
        return {tid: "running" if not task.done() else "done" for tid, task in self._active_tasks.items()}


# Глобальный экземпляр (синглтон)
task_service = TaskService()