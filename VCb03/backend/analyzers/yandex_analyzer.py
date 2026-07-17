# analyzers/yandex_analyzer.py
from typing import List, Dict, Any
from .base_analyzer import BaseHTTPAnalyzer
from config import Config

class YandexGPTAnalyzer(BaseHTTPAnalyzer):
    def __init__(self, api_key: str, folder_id: str, model: str = None, timeout: int = None):
        self.api_key = api_key
        self.folder_id = folder_id
        self.model = model or Config.YANDEX_MODEL
        super().__init__(timeout=timeout or Config.YANDEX_TIMEOUT)

    def _get_url(self) -> str:
        return Config.YANDEX_URL

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }

    def _build_payload(self, prompt: str) -> dict:
        return {
            "modelUri": f"gpt://{self.folder_id}/{self.model}",
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": 2000
            },
            "messages": [
                {"role": "user", "text": prompt}
            ]
        }

    def _extract_response(self, response_json: dict) -> str:
        return response_json['result']['alternatives'][0]['message']['text']