# tools.py
from crewai.tools import BaseTool
from ddgs import DDGS
from logger import logger


class DuckDuckGoSearchTool(BaseTool):
    name: str = "DuckDuckGoSearch"
    description: str = "Выполняет поиск в интернете через DuckDuckGo."
    max_results: int = 5

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
            logger.error(f"Ошибка поиска: {e}")
            return f"Ошибка поиска: {e}"