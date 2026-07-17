# analyzers/proxy_analyzer.py
from typing import List, Dict, Any
from .base_analyzer import BaseHTTPAnalyzer
from config import Config

class ProxyAPIAnalyzer(BaseHTTPAnalyzer):
    def __init__(self, api_key: str, base_url: str, model: str, timeout: int = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        super().__init__(timeout=timeout or Config.PROXY_TIMEOUT)

    def _get_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _build_payload(self, prompt: str) -> dict:
        return {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

    def _extract_response(self, response_json: dict) -> str:
        return response_json['choices'][0]['message']['content']