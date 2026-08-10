# 🤖 Telegram-бот на CrewAI с поддержкой внешних API и локальной LLM

Этот проект представляет собой Telegram-бота, использующего фреймворк **CrewAI** для создания многоагентных систем. Бот выполняет три основные задачи:
- **История ИИ** – генерирует хронологический обзор ключевых событий в области искусственного интеллекта за последние 10 лет.
- **История ИИ с фактчекером** – то же самое, но с дополнительной проверкой фактов через поиск DuckDuckGo.
- **SEO-анализ сайта** – сканирует веб-страницу, извлекает мета-теги, заголовки, ключевые слова и выдаёт рекомендации по оптимизации.
- **Произвольная задача** – позволяет задать любой вопрос или тему для исследования.

В качестве языковой модели (LLM) можно использовать:
- **Локальную Ollama** (запускается на вашем компьютере или сервере).
- **Внешние API**, совместимые с OpenAI (например, ProxyAPI, OpenRouter, официальный OpenAI).

**Ключевая особенность** – автоматическое ограничение модели до `gpt-3.5-turbo-16k` при использовании внешнего API.

---

## 📦 Требования

- Python 3.10+
- [Ollama](https://ollama.com/download) (если планируете использовать локальную модель)
- Telegram-бот, созданный через [@BotFather](https://t.me/botfather)
- Docker (опционально, для деплоя на VPS)

---

## ⚙️ Установка и настройка (локально)

### 1. Клонируйте репозиторий
```bash
git clone <your-repo>
cd crew_ai_history
2. Создайте виртуальное окружение и установите зависимости
bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
# или
venv\Scripts\activate      # Windows

pip install -r requirements.txt
3. Настройте переменные окружения
Скопируйте файл .env.example в .env:

bash
cp .env.example .env
Отредактируйте .env, указав свои ключи и параметры (подробнее см. раздел «Переменные окружения»).

4. Запуск бота
bash
python telegram_bot.py
🐳 Деплой на VPS через Docker
1. Сборка образа
bash
docker build -t your_dockerhub_username/crewai-telegram-bot:latest .
2. Публикация на Docker Hub
bash
docker login
docker push your_dockerhub_username/crewai-telegram-bot:latest
3. На сервере (VPS)
Установите Docker.

Создайте файл /root/.env с настройками.

Выполните:

bash
docker pull your_dockerhub_username/crewai-telegram-bot:latest
docker run -d --name crewai-bot --restart unless-stopped --env-file /root/.env your_dockerhub_username/crewai-telegram-bot:latest
4. Автоматическое обновление через Cron
Создайте скрипт /root/update_container.sh (пример есть в репозитории) и добавьте в crontab -e:

text
0 * * * * /root/update_container.sh >> /var/log/update_bot.log 2>&1
🔧 Переменные окружения (.env)
Переменная	Описание	Значение по умолчанию
OPENAI_API_KEY	Ключ API для доступа к LLM. Для Ollama используйте ollama.	ollama
OPENAI_API_BASE	Базовый URL API. Для Ollama: http://localhost:11434/v1.	http://localhost:11434/v1
OPENAI_MODEL_NAME	Название модели (например, gpt-3.5-turbo-16k, llama3.2:3b).	llama3.2:3b
BOT_TOKEN	Токен Telegram-бота (получить у @BotFather).	–
LOGTAIL_SOURCE_TOKEN	Токен для логирования в Better Stack (опционально).	–
LLM_TIMEOUT	Таймаут запроса к LLM (сек).	600
LLM_MAX_RETRIES	Максимальное количество повторных попыток при ошибке.	3
RETRY_DELAY	Начальная задержка перед повторной попыткой (сек).	2
RETRY_BACKOFF	Множитель увеличения задержки.	2
RETRY_MAX_ATTEMPTS	Максимальное число попыток (декоратор retry).	3
SEO_CACHE_TTL	Время жизни кэша для SEO-анализа (сек).	86400 (1 сутки)
MAX_CUSTOM_QUERY_LENGTH	Максимальная длина произвольного запроса (символов).	500
CREWAI_TELEMETRY_ENABLED	Включить телеметрию CrewAI.	false
📁 Структура проекта (основные файлы)
text
crew_ai_history/
├── .env.example          # Пример конфигурации
├── .dockerignore         # Исключения для Docker
├── .flake8               # Конфигурация flake8
├── .pylintrc             # Конфигурация pylint
├── .mypy.ini             # Конфигурация mypy
├── Dockerfile            # Сборка контейнера
├── docker-compose.yml    # Для локального запуска
├── update_container.sh   # Скрипт обновления на сервере
├── requirements.txt      # Зависимости
├── README.md             # Документация
├── config.py             # Централизованная конфигурация
├── logger.py             # Логирование (консоль + LogTail)
├── tools.py              # Кастомные инструменты (DuckDuckGo)
├── llm_factory.py        # Фабрика LLM
├── crews.py              # Сборка агентов и Crew
├── runners.py            # Запуск задач с повторными попытками
├── task_service.py       # Сервис управления задачами (кэш, отмена)
├── telegram_bot.py       # Основной файл бота
├── ai_history_crew.py    # Вспомогательный скрипт для теста
├── run_tests.py          # Запуск тестов
└── tests/                # Тесты (pytest)
    ├── conftest.py
    ├── test_runners.py
    └── test_telegram_bot.py
🧪 Тестирование
Для запуска тестов выполните:

bash
python run_tests.py
Или напрямую через pytest:

bash
pytest tests/ -v --cov=. --cov-report=term-missing
Тесты покрывают:

Основные функции runners.py (с моками).

Базовую логику Telegram-бота (обработчики команд).

Проверку ограничения модели.

📝 Использование бота
Отправьте команду /start – появится главное меню.

Выберите одну из кнопок:

📜 История ИИ (быстро) – создаёт обзор без фактчека.

🔎 История ИИ (с проверкой) – с фактчекером (дольше).

🔍 SEO-анализ сайта – введите URL сайта.

✍️ Произвольная задача – введите любой запрос.

Результат придёт в виде текстового сообщения или файла (если длинный).

🔒 Безопасность
Все ключи API хранятся в .env и не попадают в репозиторий.

URL для SEO-анализа валидируется перед запуском.

Длина произвольного запроса ограничена.

Контейнер Docker запускается от непривилегированного пользователя.

🤝 Вклад
Если вы хотите внести улучшения, создайте форк репозитория, внесите изменения и отправьте pull request. Для крупных изменений сначала создайте issue для обсуждения.

📄 Лицензия
MIT License. Подробнее см. файл LICENSE.

