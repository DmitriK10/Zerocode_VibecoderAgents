# agents_runner.py
import os
import time
import httpx
from functools import wraps
from pathlib import Path
from typing import Optional
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from crewai_tools import ScrapeWebsiteTool
from ddgs  import DDGS
from dotenv import load_dotenv

load_dotenv()
os.environ["OPENAI_TIMEOUT"] = "60"

# --- Декоратор повторных попыток ---
def retry_on_error(max_retries=3, delay=2, backoff=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        raise
                    wait_time = delay * (backoff ** attempt)
                    print(f"⚠️ Попытка {attempt+1} не удалась: {e}. Повтор через {wait_time:.1f} сек...")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator

# --- Кастомный инструмент поиска ---
class DuckDuckGoSearchTool(BaseTool):
    name: str = "DuckDuckGoSearch"
    description: str = "Выполняет поиск в интернете через DuckDuckGo."
    max_results: int = 5  # увеличено до 5

    def __init__(self, max_results: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.max_results = max_results

    def _run(self, query: str) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=self.max_results))
                if not results:
                    return "Ничего не найдено."
                output = []
                for r in results:
                    output.append(f"- {r.get('title', 'Без заголовка')}: {r.get('body', '')}")
                return "\n".join(output)
        except Exception as e:
            print(f"Ошибка поиска: {e}")
            return f"Ошибка поиска: {e}"

# --- Инструменты ---
search_tool = DuckDuckGoSearchTool(max_results=5)
scrape_tool = ScrapeWebsiteTool()

# --- Фабричные функции для создания агентов (переиспользование) ---
def create_researcher():
    return Agent(
        role="Исследователь истории ИИ",
        goal="Собрать наиболее значимые события, прорывы и достижения в области ИИ за последние 10 лет (2016–2026).",
        backstory=("Вы — опытный исследователь в области технологий. "
                   "Вы отслеживаете все важные новости, научные публикации и анонсы в мире ИИ."),
        verbose=False,
        allow_delegation=False,
    )

def create_analyst():
    return Agent(
        role="Аналитик трендов ИИ",
        goal="Проанализировать собранные события, выделить основные тренды, поворотные моменты и влияние на индустрию.",
        backstory=("Вы — стратегический аналитик. Вы умеете видеть связи между событиями."),
        verbose=False,
        allow_delegation=False,
    )

def create_fact_checker():
    return Agent(
        role="Фактчекер и верификатор",
        goal="Проверить достоверность фактов и при необходимости найти дополнительные источники.",
        backstory=("Вы — дотошный исследователь, который перепроверяет каждое утверждение. "
                   "Вы используете интернет-поиск через DuckDuckGo."),
        verbose=False,
        allow_delegation=False,
        tools=[search_tool],
    )

def create_writer():
    return Agent(
        role="Автор обзора",
        goal="Создать связный обзор истории ИИ за последние 10 лет с хронологией, аналитикой и прогнозом.",
        backstory=("Вы — профессиональный технический писатель."),
        verbose=False,
        allow_delegation=False,
    )

def get_ai_history_crew(enable_fact_check: bool = False) -> Crew:
    researcher = create_researcher()
    analyst = create_analyst()
    writer = create_writer()

    task1 = Task(
        description=(
            "Исследуй и составь список ключевых событий в области ИИ за последние 10 лет (2016–2026). "
            "Для каждого события укажи: год, название, краткое описание и значение. "
            "Включи: трансформеры, GPT, DALL-E, AlphaGo, AlphaFold, автономные системы, этические дебаты, регуляторные инициативы."
        ),
        agent=researcher,
        expected_output="Список событий по годам.",
    )
    task2 = Task(
        description=(
            "На основе событий выполни анализ: 1) три самых значимых прорыва; "
            "2) основные тренды (мультимодальность, вычислительные мощности, этика); "
            "3) влияние на бизнес, науку, общество. Представь структурированный отчёт."
        ),
        agent=analyst,
        expected_output="Аналитический отчёт.",
    )

    if enable_fact_check:
        fact_checker = create_fact_checker()
        task_fact_check = Task(
            description=(
                "Проверь достоверность событий и аналитики. Используй поиск для сомнительных дат/фактов. "
                "Исправь неточности, добавь пропущенные важные события. Верни обновлённый список и анализ."
            ),
            agent=fact_checker,
            expected_output="Исправленный и дополненный список событий и анализ.",
            context=[task1, task2],
        )
        task3 = Task(
            description=(
                "На основе проверенных данных создай финальный обзор истории ИИ за последние 10 лет. "
                "Включи: вступление, хронологию по годам, аналитику (прорывы, тренды, влияние), заключение с прогнозом. "
                "Стиль — информативный, доступный. Язык — русский. Формат — текст с заголовками и абзацами."
            ),
            agent=writer,
            expected_output="Полноценный обзор на русском языке.",
            context=[task_fact_check],
        )
        tasks = [task1, task2, task_fact_check, task3]
        agents = [researcher, analyst, fact_checker, writer]
    else:
        task3 = Task(
            description=(
                "На основе данных от исследователя и аналитика создай финальный обзор истории ИИ за последние 10 лет. "
                "Включи: вступление, хронологию по годам, аналитику (прорывы, тренды, влияние), заключение с прогнозом. "
                "Стиль — информативный, доступный. Язык — русский. Формат — текст с заголовками и абзацами."
            ),
            agent=writer,
            expected_output="Полноценный обзор на русском языке.",
            context=[task1, task2],
        )
        tasks = [task1, task2, task3]
        agents = [researcher, analyst, writer]

    return Crew(agents=agents, tasks=tasks, process=Process.sequential, verbose=False)

def get_seo_crew(url: str) -> Crew:
    researcher = Agent(
        role="SEO-исследователь",
        goal=f"Проанализировать сайт {url} и собрать информацию для SEO-ядра.",
        backstory="Вы эксперт по SEO. Используйте инструмент ScrapeWebsiteTool для получения HTML-кода страницы, затем извлеките мета-теги, заголовки, текстовое содержимое, выделите основные темы и потенциальные ключевые слова.",
        verbose=False,
        allow_delegation=False,
        tools=[scrape_tool],
    )
    analyst = Agent(
        role="SEO-аналитик",
        goal="Составить список ключевых слов и рекомендаций.",
        backstory="Вы опытный SEO-специалист.",
        verbose=False,
        allow_delegation=False,
    )
    task1 = Task(
        description=f"Проанализируй сайт по URL: {url}. Используй инструмент ScrapeWebsiteTool, чтобы получить содержимое страницы. Затем извлеки мета-теги (title, description), заголовки (H1-H6), текстовое содержимое, выдели основные темы и потенциальные ключевые слова. Верни структурированный отчёт.",
        agent=researcher,
        expected_output="Список ключевых слов, мета-теги, структура заголовков, основные темы.",
    )
    task2 = Task(
        description="На основе анализа составь SEO-ядро (ключевые слова, рекомендации по улучшению мета-тегов, структуры URL, контента).",
        agent=analyst,
        expected_output="SEO-ядро и рекомендации.",
        context=[task1],
    )
    return Crew(agents=[researcher, analyst], tasks=[task1, task2], process=Process.sequential, verbose=False)

def check_url_availability(url: str, timeout: int = 10) -> bool:
    """Проверяет доступность URL с помощью HEAD-запроса."""
    try:
        response = httpx.head(url, timeout=timeout, follow_redirects=True)
        return response.status_code < 400
    except Exception:
        return False

@retry_on_error(max_retries=3, delay=2)
def run_ai_history(enable_fact_check: bool = False) -> str:
    crew = get_ai_history_crew(enable_fact_check=enable_fact_check)
    result = crew.kickoff()
    return str(result)

@retry_on_error(max_retries=3, delay=2)
def run_seo_analysis(url: str) -> str:
    # Проверка доступности сайта перед запуском агентов
    if not check_url_availability(url):
        return f"❌ Сайт {url} недоступен. Проверьте URL или попробуйте позже."
    crew = get_seo_crew(url)
    result = crew.kickoff()
    return str(result)

@retry_on_error(max_retries=3, delay=2)
def run_custom_task(task_description: str) -> str:
    researcher = Agent(
        role="Исследователь",
        goal="Изучить задачу и собрать необходимую информацию.",
        backstory="Вы опытный исследователь.",
        verbose=False,
        allow_delegation=False,
        tools=[search_tool],
    )
    writer = Agent(
        role="Автор отчёта",
        goal="На основе исследования подготовить структурированный ответ.",
        backstory="Вы профессиональный писатель.",
        verbose=False,
        allow_delegation=False,
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
    return str(result)