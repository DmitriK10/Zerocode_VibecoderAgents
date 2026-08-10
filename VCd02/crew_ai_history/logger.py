# logger.py
import logging
import os

from config import settings


class AppLogger:
    """Централизованный логгер с поддержкой консоли и LogTail."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, name: str = 'crewai_bot'):
        if self._initialized:
            return
        self._initialized = True
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Консольный хендлер
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        self.logger.addHandler(console)

        # LogTail
        if settings.logtail_source_token:
            try:
                from logtail import LogtailHandler
                lt_handler = LogtailHandler(source_token=settings.logtail_source_token)
                lt_handler.setLevel(logging.INFO)
                self.logger.addHandler(lt_handler)
                self.logger.info('LogTail handler добавлен')
            except ImportError:
                self.logger.warning('Библиотека logtail не установлена')
            except Exception as e:
                self.logger.error(f'Ошибка инициализации LogTail: {e}')

    def get_logger(self):
        return self.logger


logger = AppLogger().get_logger()