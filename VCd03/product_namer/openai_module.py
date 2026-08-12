"""
Модуль для работы с LLM через Proxy API.
Реализует клиент с методами chat, chat_with_system, chat_json.
Соблюдает Single Responsibility: только общение с API.
Принудительно отключает системные прокси через переменные окружения.
"""
import os
import json
import logging
from typing import Optional, Dict, Any

from openai import OpenAI
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai

# Загружаем переменные из .env
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://api.proxypi.ru/v1")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-16k")

if not API_KEY:
    raise ValueError("API_KEY не задан в .env")

# ---------- НАСТРОЙКА ЛОГИРОВАНИЯ ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"BASE_URL: {BASE_URL}")
logger.info(f"MODEL: {MODEL}")
logger.info(f"API_KEY: {API_KEY[:4]}..." if API_KEY else "API_KEY не задан")

# ---------- ОТКЛЮЧЕНИЕ ПРОКСИ ----------
# Убираем переменные прокси, чтобы запросы шли напрямую
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["ALL_PROXY"] = ""
os.environ["NO_PROXY"] = "*"
logger.info("Переменные прокси принудительно обнулены")


class LLMClient:
    """
    Клиент для взаимодействия с LLM через Proxy API.
    Инкапсулирует создание клиента OpenAI и методы запросов.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.base_url = base_url or BASE_URL
        self.api_key = api_key or API_KEY
        self.model = model or MODEL

        # Создаём клиент OpenAI (будет использовать обнулённые переменные прокси)
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APIError, openai.APIConnectionError)),
        reraise=True,
    )
    def chat(self, prompt: str, max_tokens: int = 500) -> str:
        logger.info("Отправка простого запроса к LLM")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Ошибка в chat: {type(e).__name__}: {e}", exc_info=True)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APIError, openai.APIConnectionError)),
        reraise=True,
    )
    def chat_with_system(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 500
    ) -> str:
        logger.info("Отправка запроса с системным промптом")
        logger.debug(f"System prompt (первые 200 символов): {system_prompt[:200]}...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Ошибка в chat_with_system: {type(e).__name__}: {e}", exc_info=True)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APIError, openai.APIConnectionError)),
        reraise=True,
    )
    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: Optional[Dict[str, Any]] = None,
        max_tokens: int = 800,
    ) -> Dict[str, Any]:
        logger.info("Отправка запроса с требованием JSON")
        enhanced_system = (
            system_prompt
            + "\n\nВерни ответ строго в формате JSON без дополнительного текста."
        )
        try:
            response_text = self.chat_with_system(enhanced_system, user_prompt, max_tokens)
            # Ищем JSON
            start = response_text.find("{")
            if start == -1:
                start = response_text.find("[")
            if start == -1:
                raise ValueError("Ответ не содержит JSON")
            end = response_text.rfind("}")
            if end == -1:
                end = response_text.rfind("]")
            if end == -1:
                raise ValueError("Ответ не содержит JSON")
            json_str = response_text[start:end+1]
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}. Ответ: {response_text[:500]}...")
            raise ValueError("Некорректный JSON в ответе LLM") from e
        except Exception as e:
            logger.error(f"Ошибка в chat_json: {type(e).__name__}: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    client = LLMClient()
    try:
        print("Пробный запрос 'chat':")
        resp = client.chat("Привет! Как дела?")
        print(resp)
        print("\nПробный запрос 'chat_json':")
        sys_prompt = "Ты помощник. Ответь на вопрос в формате JSON с ключами 'answer' и 'confidence'."
        user_prompt = "Сколько будет 2+2?"
        json_resp = client.chat_json(sys_prompt, user_prompt)
        print(json_resp)
    except Exception as e:
        print(f"Ошибка: {e}")