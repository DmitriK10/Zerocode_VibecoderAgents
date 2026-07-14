# 🤖 Telegram-бот с ИИ-помощником через ProxyAPI

Бот использует модель `gpt-4o-mini` через российский агрегатор **ProxyAPI**.
Отвечает на любые текстовые сообщения, выступая в роли вежливого и профессионального ассистента.

## 🛠 Требования

- Python 3.8+
- Аккаунт на [ProxyAPI](https://proxyapi.ru) с пополненным балансом (или промокод)
- Токен Telegram-бота от [@BotFather](https://t.me/botfather)

## 📥 Установка и запуск

1. **Клонируйте репозиторий** или скопируйте файлы в папку проекта.

2. **Создайте виртуальное окружение** (рекомендуется):
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Linux/Mac
   .venv\Scripts\activate         # Windows
Установите зависимости:

bash
pip install -r requirements.txt
Настройте переменные окружения:

Переименуйте .env.example в .env.

Вставьте свои токены и ключи:

text
BOT_TOKEN=ваш_токен
OPENAI_API_KEY=ваш_ключ_ProxyAPI
OPENAI_BASE_URL=https://api.proxyapi.ru/openai/v1
OPENAI_MODEL=gpt-4o-mini
Запустите бота:

bash
python bot.py
В Telegram найдите своего бота и отправьте /start.

🧠 Использование
Просто напишите боту любой вопрос.

Он ответит, используя модель gpt-4o-mini через ProxyAPI.

Все диалоги логируются в файл bot.log.

📊 Мониторинг баланса
Проверяйте расход средств в личном кабинете ProxyAPI. Цены: ~36 ₽ за 1M токенов запроса, ~146 ₽ за 1M токенов ответа (для gpt-4o-mini).

📄 Лицензия
Проект создан в образовательных целях.

