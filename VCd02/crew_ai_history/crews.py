# crews.py
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import ScrapeWebsiteTool
from typing import Optional

from tools import DuckDuckGoSearchTool
from llm_factory import get_llm


def create_researcher(llm: Optional[LLM] = None):
    llm = llm or get_llm()
    return Agent(
        role="Исследователь истории ИИ",
        goal="Собрать наиболее значимые события, прорывы и достижения в области ИИ за последние 10 лет (2016–2026).",
        backstory=(
            "Вы — опытный исследователь в области технологий. "
            "Вы отслеживаете все важные новости, научные публикации и анонсы в мире ИИ."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm,
    )


def create_analyst(llm: Optional[LLM] = None):
    llm = llm or get_llm()
    return Agent(
        role="Аналитик трендов ИИ",
        goal="Проанализировать собранные события, выделить основные тренды, поворотные моменты и влияние на индустрию.",
        backstory=("Вы — стратегический аналитик. Вы умеете видеть связи между событиями."),
        verbose=False,
        allow_delegation=False,
        llm=llm,
    )


def create_fact_checker(llm: Optional[LLM] = None):
    llm = llm or get_llm()
    return Agent(
        role="Фактчекер и верификатор",
        goal="Проверить достоверность фактов и при необходимости найти дополнительные источники.",
        backstory=(
            "Вы — дотошный исследователь, который перепроверяет каждое утверждение. "
            "Вы используете интернет-поиск через DuckDuckGo."
        ),
        verbose=False,
        allow_delegation=False,
        tools=[DuckDuckGoSearchTool(max_results=5)],
        llm=llm,
    )


def create_writer(llm: Optional[LLM] = None):
    llm = llm or get_llm()
    return Agent(
        role="Автор обзора",
        goal="Создать связный обзор истории ИИ за последние 10 лет с хронологией, аналитикой и прогнозом.",
        backstory=("Вы — профессиональный технический писатель."),
        verbose=False,
        allow_delegation=False,
        llm=llm,
    )


def get_ai_history_crew(enable_fact_check: bool = False) -> Crew:
    llm = get_llm()
    researcher = create_researcher(llm)
    analyst = create_analyst(llm)
    writer = create_writer(llm)

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
        fact_checker = create_fact_checker(llm)
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
    llm = get_llm()
    researcher = Agent(
        role="SEO-исследователь",
        goal=f"Проанализировать сайт {url} и собрать информацию для SEO-ядра.",
        backstory="Вы эксперт по SEO. Используйте инструмент ScrapeWebsiteTool для получения HTML-кода страницы, затем извлеките мета-теги, заголовки, текстовое содержимое, выделите основные темы и потенциальные ключевые слова.",
        verbose=False,
        allow_delegation=False,
        tools=[ScrapeWebsiteTool()],
        llm=llm,
    )
    analyst = Agent(
        role="SEO-аналитик",
        goal="Составить список ключевых слов и рекомендаций.",
        backstory="Вы опытный SEO-специалист.",
        verbose=False,
        allow_delegation=False,
        llm=llm,
    )
    task1 = Task(
        description=(
            f"Проанализируй сайт по URL: {url}. Используй инструмент ScrapeWebsiteTool, чтобы получить содержимое страницы. "
            "Затем извлеки мета-теги (title, description), заголовки (H1-H6), текстовое содержимое, выдели основные темы и потенциальные ключевые слова. Верни структурированный отчёт."
        ),
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