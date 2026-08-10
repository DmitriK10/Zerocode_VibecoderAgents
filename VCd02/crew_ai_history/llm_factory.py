# llm_factory.py
from crewai import LLM
from config import settings
from logger import logger


def get_llm() -> LLM:
    """
    Создаёт экземпляр LLM с учётом ограничения модели.
    Если используется не Ollama, модель принудительно устанавливается gpt-3.5-turbo-16k.
    """
    base_url = settings.openai_api_base
    api_key = settings.openai_api_key
    model_name = settings.openai_model_name

    # Ограничение модели при использовании внешнего API
    if api_key != "ollama" and not model_name.startswith("gpt-3.5"):
        logger.warning(
            f"Модель {model_name} превышает допустимый лимит. "
            "Принудительно установлена gpt-3.5-turbo-16k."
        )
        model_name = "gpt-3.5-turbo-16k"

    # Для Ollama не добавляем префикс, для остальных – добавляем "openai/"
    if api_key != "ollama":
        model_full = f"openai/{model_name}"
    else:
        model_full = model_name

    return LLM(
        model=model_full,
        base_url=base_url,
        api_key=api_key,
        timeout=settings.llm_timeout,
        max_retries=settings.llm_max_retries,
    )