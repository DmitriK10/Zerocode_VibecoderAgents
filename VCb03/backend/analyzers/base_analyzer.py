# analyzers/base_analyzer.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import requests
import logging

logger = logging.getLogger(__name__)

class BaseLLMAnalyzer(ABC):
    """Абстрактный базовый класс для всех анализаторов LLM."""

    @abstractmethod
    def analyze(self, table_data: List[Dict[str, Any]]) -> str:
        pass


class BaseHTTPAnalyzer(BaseLLMAnalyzer):
    """
    Базовый класс для анализаторов, использующих HTTP-запросы к LLM API.
    Подклассы должны определить url, headers, build_payload.
    """
    def __init__(self, timeout: int = 60):
        self.timeout = timeout

    @abstractmethod
    def _get_url(self) -> str:
        pass

    @abstractmethod
    def _get_headers(self) -> dict:
        pass

    @abstractmethod
    def _build_payload(self, prompt: str) -> dict:
        pass

    def _extract_response(self, response_json: dict) -> str:
        """Извлекает текст ответа из JSON. Должен быть переопределён при необходимости."""
        raise NotImplementedError

    def analyze(self, table_data: List[Dict[str, Any]]) -> str:
        if not table_data:
            return "Нет данных для анализа."

        # Формируем промпт (можно переопределить в подклассах)
        rows_text = "\n".join([str(row) for row in table_data[:15]])
        prompt = (
            "Ты - аналитическая система с большим опытом. Твоя задача - анализировать табличные данные, "
            "делать выводы и находить аномалии или интересные тенденции.\n"
            "Вот первые 15 строк таблицы:\n" + rows_text
        )

        url = self._get_url()
        headers = self._get_headers()
        payload = self._build_payload(prompt)

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            result = resp.json()
            return self._extract_response(result)
        except requests.exceptions.Timeout:
            logger.error("Таймаут при запросе к LLM")
            return "⚠️ Превышено время ожидания ответа от модели."
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка HTTP: {e}")
            return f"⚠️ Ошибка при запросе к LLM: {str(e)}"
        except Exception as e:
            logger.error(f"Неизвестная ошибка: {e}")
            return f"⚠️ Произошла ошибка: {str(e)}"