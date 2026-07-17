# analyzers/factory.py
from .base_analyzer import BaseLLMAnalyzer
from .yandex_analyzer import YandexGPTAnalyzer
from .proxy_analyzer import ProxyAPIAnalyzer
from config import Config

class AnalyzerFactory:
    _registry = {
        'yandex': lambda config: YandexGPTAnalyzer(
            api_key=config.YANDEX_API_KEY,
            folder_id=config.YANDEX_FOLDER_ID,
            model=getattr(config, 'YANDEX_MODEL', None),
            timeout=getattr(config, 'YANDEX_TIMEOUT', None)
        ),
        'proxy': lambda config: ProxyAPIAnalyzer(
            api_key=config.PROXY_API_KEY,
            base_url=config.PROXY_BASE_URL,
            model=config.PROXY_MODEL,
            timeout=getattr(config, 'PROXY_TIMEOUT', None)
        )
    }

    @staticmethod
    def get_analyzer(model_name: str, config: Config) -> BaseLLMAnalyzer:
        if model_name not in AnalyzerFactory._registry:
            raise ValueError(f"Unknown model: {model_name}")
        return AnalyzerFactory._registry[model_name](config)