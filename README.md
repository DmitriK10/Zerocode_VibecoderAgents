# Вайб-кодинг и автономные агенты — учебные проекты

12 проектов курса **«Вайб-кодинг и автономные агенты»** (Zerocoder): от простых приложений на Python до многоагентных систем на CrewAI с локальной моделью через Ollama.

Каждая папка — отдельный проект со своим `README.md`, `.env.example` и `requirements.txt`. Всё запускается локально.

## Чем интересен этот репозиторий

Здесь видно, как один и тот же класс задач решается разными способами и с разной степенью автономности:

| Этап | Что меняется | Проекты |
|---|---|---|
| Приложения на Python | Обычная разработка: GUI, веб, Telegram | `VCa01`–`VCa03` |
| Подключение LLM | Модель отвечает в чате | `VCb01`–`VCb03` |
| Данные и агенты | Модель работает с файлами, БД, контейнерами | `VCc01`–`VCc03` |
| Автономные агенты | Многоагентные команды, локальная модель, тесты | `VCd01`–`VCd03` |

Полезнее всего для портфолио:

- **[VCc02](VCc02/obsidian-analyzer/)** — Obsidian Note Analyzer: Flask + Nginx + Telegram-бот в Docker Compose, анализ хранилища заметок. Многоконтейнерное приложение, а не один скрипт.
- **[VCd02](VCd02/crew_ai_history/)** — CrewAI-бот с внешними API и локальной LLM: тесты, линтеры (`flake8`, `mypy`, `pylint`), Docker, логирование.
- **[VCb03](VCb03/)** — Data Analyzer: загрузка Excel/CSV/PDF, визуализация и аналитика через LLM.

## Проекты

### Модуль A — приложения на Python

| Папка | Проект | Стек |
|---|---|---|
| [VCa01](VCa01/) | Генератор паролей с графическим интерфейсом: длина 4–64, выбор наборов символов | Python, GUI |
| [VCa02](VCa02/) | Ипотечный калькулятор с досрочными погашениями, тёмная «барочная» тема | Flask, HTML/CSS |
| [VCa03](VCa03/) | Telegram-бот поиска рецептов: TheMealDB API, избранное, рейтинг 1–5 | Python, SQLite |

### Модуль B — нейросети в приложениях

| Папка | Проект | Стек |
|---|---|---|
| [VCb01](VCb01/) | Telegram-бот с ИИ-помощником через ProxyAPI (`gpt-4o-mini`) | aiogram, ProxyAPI |
| [VCb02](VCb02/) | Telegram-бот с двумя моделями: GigaChat и YandexGPT, переключение inline-кнопкой | aiogram, GigaChat API, YandexGPT |
| [VCb03](VCb03/) | Data Analyzer: загрузка `.xlsx/.xls/.csv/.pdf`, извлечение таблиц из PDF, интерактивная таблица, аналитика через LLM | Flask + React, YandexGPT |

### Модуль C — данные, контейнеры, агенты

| Папка | Проект | Стек |
|---|---|---|
| [VCc01](VCc01/) | Telegram-бот сбора анкет: PostgreSQL + Excel + SQLite, модульная архитектура по SOLID | pyTelegramBotAPI, PostgreSQL |
| [VCc02](VCc02/) | Obsidian Note Analyzer: дашборд статистики по хранилищу, дайджест изменений в Telegram | Flask, Nginx, aiogram, MCP, Docker Compose |
| [VCc03](VCc03/) | Telegram-бот на CrewAI: обзор истории ИИ, фактчекинг через DuckDuckGo, SEO-анализ сайта | CrewAI, Telegram |

### Модуль D — автономные агенты

| Папка | Проект | Стек |
|---|---|---|
| [VCd01](VCd01/) | Тот же CrewAI-бот, но на локальной модели через Ollama — данные не уходят в облако | CrewAI, Ollama, тесты |
| [VCd02](VCd02/) | CrewAI-бот с гибким выбором: внешние API или локальная LLM, фактчекинг, произвольные задачи | CrewAI, Docker, pytest, flake8, mypy, pylint |
| [VCd03](VCd03/) | Product Namer Agent: по URL страницы генерирует 5 названий продукта, полная типизация, DI, тесты | Python, OpenAI API, pytest |

## Как запустить любой проект

1. Перейти в папку проекта и создать окружение:

   ```bash
   cd VCd02/crew_ai_history
   python -m venv venv
   source venv/bin/activate      # Linux / macOS
   venv\Scripts\activate         # Windows
   ```

2. Установить зависимости:

   ```bash
   pip install -r requirements.txt
   ```

3. Скопировать `.env.example` в `.env` и заполнить ключи — у каждого проекта свой набор (Telegram Bot Token, ключ GigaChat / YandexGPT / ProxyAPI, доступ к БД).

4. Запустить по инструкции из `README.md` проекта. Проекты на Docker Compose (`VCc02`) поднимаются командой `docker compose up -d`.

## Требования

- Python 3.10+
- Docker и Docker Compose — для `VCc02`
- Ollama — для `VCd01` (локальная модель)
- Аккаунты и ключи: Telegram Bot Token, GigaChat / YandexGPT / ProxyAPI, DuckDuckGo — без ключа

## Безопасность

Ключи и токены в репозитории не хранятся: в проектах лежит только `.env.example` с заглушками, реальные значения — в `.env`, который в `.gitignore`.

## Лицензия

MIT — см. [LICENSE](LICENSE).
