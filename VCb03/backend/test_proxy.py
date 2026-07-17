import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('PROXY_API_KEY')
BASE_URL = os.getenv('PROXY_BASE_URL', 'https://api.proxyapi.ru/openai/v1')

models_to_try = [
    'gpt-4o-mini',
    'gpt-4-turbo',
    'deepseek-chat',
    'deepseek-reasoner',
    'claude-3.5-sonnet',
    'gpt-3.5-turbo'
]

url = f"{BASE_URL}/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

for model in models_to_try:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Привет!"}],
        "max_tokens": 50
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            print(f"✅ Модель {model} работает!")
            print(f"   Ответ: {resp.json()['choices'][0]['message']['content'][:50]}...")
            break
        else:
            print(f"❌ Модель {model} не поддерживается (статус {resp.status_code})")
    except Exception as e:
        print(f"⚠️ Ошибка при запросе к {model}: {e}")