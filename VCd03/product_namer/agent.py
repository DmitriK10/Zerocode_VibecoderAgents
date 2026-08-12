"""
Агент для подбора названий продукта по URL-адресу.
Загружает страницу, извлекает текст, отправляет запрос к LLM и возвращает 5 вариантов названий.
Добавлено подробное логирование для диагностики.
"""
import logging
from typing import List, Dict, Optional, Any

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from openai_module import LLMClient

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentError(Exception):
    """Базовое исключение для ошибок агента."""
    pass


class PageLoadError(AgentError):
    """Ошибка загрузки страницы."""
    pass


class ParsingError(AgentError):
    """Ошибка парсинга HTML."""
    pass


class LLMResponseError(AgentError):
    """Ошибка получения или парсинга ответа от LLM."""
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException,)),
    reraise=True,
)
def fetch_html(url: str) -> str:
    """
    Загружает HTML-код страницы по URL.

    :param url: адрес страницы
    :return: HTML в виде строки
    :raises PageLoadError: если загрузка не удалась
    """
    try:
        logger.info(f"Загрузка страницы: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        logger.debug(f"Загружено {len(response.text)} байт HTML")
        return response.text
    except requests.RequestException as e:
        logger.error(f"Ошибка загрузки {url}: {e}", exc_info=True)
        raise PageLoadError(f"Не удалось загрузить страницу: {e}") from e


def extract_text_from_html(html: str) -> str:
    """
    Извлекает чистый текст из HTML, удаляя теги и лишние пробелы.

    :param html: HTML-код
    :return: очищенный текст
    :raises ParsingError: если парсинг не удался
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        # Удаляем скрипты и стили
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator=" ", strip=True)
        # Удаляем множественные пробелы и переносы
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)
        if not text:
            raise ParsingError("После очистки текст пуст")
        logger.debug(f"Извлечено {len(text)} символов текста")
        return text
    except Exception as e:
        logger.error(f"Ошибка парсинга HTML: {e}", exc_info=True)
        raise ParsingError(f"Не удалось распарсить HTML: {e}") from e


def run(url: str, llm_client: Optional[LLMClient] = None) -> List[Dict[str, str]]:
    """
    Основная функция агента. Загружает страницу, анализирует и возвращает 5 названий.

    :param url: URL страницы с описанием продукта
    :param llm_client: экземпляр LLMClient (если None, создаётся новый)
    :return: список словарей с ключами 'name' и 'reason'
    :raises AgentError: при любой ошибке в процессе
    """
    if llm_client is None:
        logger.info("Создаём новый LLMClient по умолчанию")
        llm_client = LLMClient()  # создаём клиент по умолчанию

    # Шаг 1: загружаем HTML
    logger.info("Шаг 1: загрузка HTML")
    html = fetch_html(url)

    # Шаг 2: извлекаем текст
    logger.info("Шаг 2: извлечение текста из HTML")
    page_text = extract_text_from_html(html)
    # Ограничим длину текста, чтобы не превысить контекст модели
    if len(page_text) > 8000:
        logger.warning("Текст слишком длинный, обрезаем до 8000 символов")
        page_text = page_text[:8000]
    logger.info(f"Размер текста для отправки: {len(page_text)} символов")

    # Шаг 3: формируем системный промпт
    system_prompt = (
        "Ты креативный маркетолог, специализирующийся на нейминге. "
        "На основе описания продукта предложи 5 вариантов названия. "
        "Каждое название должно быть уникальным, запоминающимся и соответствовать сути продукта. "
        "Верни ответ строго в формате JSON, где ключ 'names' содержит массив объектов, "
        "каждый с полями 'name' (название) и 'reason' (краткое объяснение, почему оно подходит)."
    )

    user_prompt = (
        f"Вот описание продукта (взято с веб-страницы):\n\n{page_text}\n\n"
        "Предложи 5 названий для этого продукта."
    )

    logger.debug(f"Системный промпт: {system_prompt[:200]}...")
    logger.debug(f"Пользовательский промпт (первые 200 символов): {user_prompt[:200]}...")

    # Шаг 4: отправляем запрос к LLM и парсим ответ
    try:
        logger.info("Шаг 4: отправка запроса к LLM для генерации названий")
        response_dict = llm_client.chat_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=800,
        )
        logger.debug(f"Ответ от LLM (полный): {response_dict}")
    except Exception as e:
        logger.error(f"Ошибка при запросе к LLM: {type(e).__name__}: {e}", exc_info=True)
        raise LLMResponseError(f"Ошибка LLM: {e}") from e

    # Шаг 5: извлекаем список названий
    logger.info("Шаг 5: извлечение названий из ответа")
    names_data = response_dict.get("names")
    if not isinstance(names_data, list):
        logger.error(f"Неверный формат ответа LLM: {response_dict}")
        raise LLMResponseError("Ответ LLM не содержит поле 'names' или оно не является списком")

    # Проверим, что каждый элемент имеет нужные поля
    result = []
    for item in names_data:
        if not isinstance(item, dict):
            logger.warning(f"Пропускаем элемент, не являющийся словарём: {item}")
            continue
        name = item.get("name")
        reason = item.get("reason", "")
        if name:
            result.append({"name": name, "reason": reason})
        else:
            logger.warning(f"Пропускаем элемент без поля 'name': {item}")

    if len(result) < 5:
        logger.warning(f"LLM вернула только {len(result)} названий, ожидалось 5")
    else:
        logger.info(f"Успешно получено {len(result)} названий")

    return result


# Точка входа для командной строки: python agent.py <url>
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Использование: python agent.py <URL>")
        sys.exit(1)
    target_url = sys.argv[1]
    try:
        result = run(target_url)
        print("\n" + "="*50)
        print("Получены названия:")
        for idx, item in enumerate(result, 1):
            print(f"{idx}. {item['name']} — {item['reason']}")
        print("="*50)
    except AgentError as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)