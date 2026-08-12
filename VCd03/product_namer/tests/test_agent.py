"""
Модульные тесты для агента подбора названий продукта.

Тесты покрывают:
- Успешный сценарий работы агента.
- Ошибки загрузки страницы.
- Ошибки при ответе LLM (невалидный JSON, отсутствие поля 'names', недостаточное количество названий).
- Корректность парсинга HTML.
- Обработку пустого HTML.
"""
import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path для корректного импорта модулей
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import MagicMock, patch

from agent import run, fetch_html, extract_text_from_html, AgentError, LLMResponseError
from openai_module import LLMClient


@pytest.fixture
def mock_llm_client():
    """
    Фикстура, создающая заглушку для LLMClient.

    Возвращает объект MagicMock, который имитирует поведение LLMClient.
    По умолчанию метод chat_json возвращает корректный JSON с 5 названиями.
    Это позволяет тестировать логику агента без реальных вызовов API.
    """
    client = MagicMock(spec=LLMClient)
    client.chat_json.return_value = {
        "names": [
            {"name": "Название1", "reason": "Причина1"},
            {"name": "Название2", "reason": "Причина2"},
            {"name": "Название3", "reason": "Причина3"},
            {"name": "Название4", "reason": "Причина4"},
            {"name": "Название5", "reason": "Причина5"},
        ]
    }
    return client


def test_run_success(mock_llm_client):
    """
    Тест успешного выполнения агента.

    Проверяет, что при корректном URL и работающей LLM агент:
    1. Загружает HTML (мокаем fetch_html).
    2. Извлекает текст (мокаем extract_text_from_html).
    3. Отправляет запрос к LLM через chat_json.
    4. Возвращает список из 5 словарей с полями 'name' и 'reason'.
    5. Содержимое соответствует данным из заглушки.
    """
    url = "https://example.com/product"

    # Подменяем реальные функции загрузки и парсинга, чтобы не ходить в сеть
    with patch("agent.fetch_html", return_value="<html><body>Описание продукта</body></html>"):
        with patch("agent.extract_text_from_html", return_value="Описание продукта"):
            result = run(url, llm_client=mock_llm_client)

    # Проверяем количество названий
    assert len(result) == 5, f"Ожидалось 5 названий, получено {len(result)}"

    # Проверяем структуру и содержимое первого элемента
    assert result[0]["name"] == "Название1", "Название не соответствует заглушке"
    assert result[0]["reason"] == "Причина1", "Причина не соответствует заглушке"

    # Убеждаемся, что метод chat_json был вызван ровно один раз
    mock_llm_client.chat_json.assert_called_once()


def test_run_fetch_fails(mock_llm_client):
    """
    Тест ситуации, когда загрузка страницы завершается ошибкой.

    Проверяет, что если fetch_html выбрасывает исключение AgentError,
    то функция run также выбрасывает AgentError, а не обрабатывает ошибку молча.
    """
    with patch("agent.fetch_html", side_effect=AgentError("Ошибка загрузки")):
        with pytest.raises(AgentError, match="Ошибка загрузки"):
            run("http://fail.com", llm_client=mock_llm_client)


def test_run_llm_returns_invalid_json(mock_llm_client):
    """
    Тест ошибки, когда LLM возвращает невалидный JSON.

    Если chat_json выбрасывает ValueError (например, из-за невозможности распарсить JSON),
    то run должен обернуть это исключение в LLMResponseError.
    """
    mock_llm_client.chat_json.side_effect = ValueError("Некорректный JSON")

    with patch("agent.fetch_html", return_value="<html><body>text</body></html>"):
        with patch("agent.extract_text_from_html", return_value="text"):
            with pytest.raises(LLMResponseError, match="Ошибка LLM"):
                run("http://example.com", llm_client=mock_llm_client)


def test_run_llm_returns_missing_names(mock_llm_client):
    """
    Тест, когда LLM возвращает корректный JSON, но без ключа 'names'.

    В этом случае агент должен выбросить исключение LLMResponseError
    с соответствующим сообщением.
    """
    mock_llm_client.chat_json.return_value = {"other": "data"}

    with patch("agent.fetch_html", return_value="<html><body>text</body></html>"):
        with patch("agent.extract_text_from_html", return_value="text"):
            with pytest.raises(LLMResponseError, match="не содержит поле 'names'"):
                run("http://example.com", llm_client=mock_llm_client)


def test_run_llm_returns_less_than_5(mock_llm_client):
    """
    Тест, когда LLM возвращает менее 5 названий (например, только 2).

    Агент должен вернуть то, что есть, без выбрасывания исключения,
    но при этом может залогировать предупреждение (мы не проверяем логи).
    """
    mock_llm_client.chat_json.return_value = {
        "names": [
            {"name": "Название1", "reason": "Причина1"},
            {"name": "Название2", "reason": "Причина2"},
        ]
    }

    with patch("agent.fetch_html", return_value="<html><body>text</body></html>"):
        with patch("agent.extract_text_from_html", return_value="text"):
            result = run("http://example.com", llm_client=mock_llm_client)

    # Ожидаем, что вернётся 2 названия (ровно столько, сколько отдала LLM)
    assert len(result) == 2, f"Ожидалось 2 названия, получено {len(result)}"
    assert result[0]["name"] == "Название1"
    assert result[1]["name"] == "Название2"


def test_extract_text_from_html():
    """
    Тест функции извлечения текста из HTML.

    Проверяет, что функция корректно удаляет теги и возвращает весь видимый текст,
    включая содержимое тегов <title>, <head> и т.д.
    """
    html = "<html><head><title>Test</title></head><body><p>Hello, world!</p></body></html>"
    text = extract_text_from_html(html)

    # Функция возвращает весь текст, поэтому проверяем наличие ключевых подстрок
    assert "Test" in text, "Текст из <title> не найден"
    assert "Hello, world!" in text, "Текст из <body> не найден"


def test_extract_text_empty():
    """
    Тест обработки пустого HTML.

    Если после очистки текст оказывается пустым, функция должна выбрасывать ParsingError
    (который является наследником AgentError) с соответствующим сообщением.
    """
    html = "<html><body></body></html>"
    with pytest.raises(AgentError, match="текст пуст"):
        extract_text_from_html(html)