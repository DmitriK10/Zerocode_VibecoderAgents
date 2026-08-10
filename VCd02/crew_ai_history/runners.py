# runners.py
import time
from functools import wraps
from typing import Callable

from config import settings
from logger import logger
from crews import get_ai_history_crew, get_seo_crew
import httpx


def retry_on_error(max_attempts: int = None, delay: int = None, backoff: int = None):
    """Декоратор повторных попыток с параметрами из конфига."""
    max_attempts = max_attempts or settings.retry_max_attempts
    delay = delay or settings.retry_delay
    backoff = backoff or settings.retry_backoff

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        raise
                    wait_time = delay * (backoff ** attempt)
                    logger.warning(
                        f"Попытка {attempt+1} не удалась: {e}. Повтор через {wait_time:.1f} сек..."
                    )
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator


def check_url_availability(url: str, timeout: int = 10) -> bool:
    """Проверяет доступность URL через HEAD-запрос."""
    try:
        response = httpx.head(url, timeout=timeout, follow_redirects=True)
        return response.status_code < 400
    except Exception:
        return False


@retry_on_error()
def run_ai_history(enable_fact_check: bool = False) -> str:
    logger.info(f"Запуск run_ai_history с fact_check={enable_fact_check}")
    crew = get_ai_history_crew(enable_fact_check=enable_fact_check)
    result = crew.kickoff()
    logger.info("run_ai_history завершён")
    return str(result)


@retry_on_error()
def run_seo_analysis(url: str) -> str:
    logger.info(f"Запуск SEO-анализа для {url}")
    if not check_url_availability(url):
        msg = f"❌ Сайт {url} недоступен. Проверьте URL или попробуйте позже."
        logger.warning(msg)
        return msg
    crew = get_seo_crew(url)
    result = crew.kickoff()
    logger.info("SEO-анализ завершён")
    return str(result)


@retry_on_error()
def run_custom_task(task_description: str) -> str:
    logger.info(f"Запуск произвольной задачи: {task_description[:100]}...")
    from llm_factory import get_llm
    from crewai import Agent, Task, Crew, Process
    from tools import DuckDuckGoSearchTool

    llm = get_llm()
    researcher = Agent(
        role="Исследователь",
        goal="Изучить задачу и собрать необходимую информацию.",
        backstory="Вы опытный исследователь.",
        verbose=False,
        allow_delegation=False,
        tools=[DuckDuckGoSearchTool(max_results=5)],
        llm=llm,
    )
    writer = Agent(
        role="Автор отчёта",
        goal="На основе исследования подготовить структурированный ответ.",
        backstory="Вы профессиональный писатель.",
        verbose=False,
        allow_delegation=False,
        llm=llm,
    )
    task1 = Task(
        description=f"Изучи следующую задачу: {task_description}. Собери релевантную информацию, факты, данные.",
        agent=researcher,
        expected_output="Исследовательские данные.",
    )
    task2 = Task(
        description=f"На основе исследования подготовь развернутый ответ по задаче: {task_description}. Ответ должен быть информативным, структурированным и на русском языке.",
        agent=writer,
        expected_output="Ответ на задачу.",
        context=[task1],
    )
    crew = Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential, verbose=False)
    result = crew.kickoff()
    logger.info("Произвольная задача завершена")
    return str(result)