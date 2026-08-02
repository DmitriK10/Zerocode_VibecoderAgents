"""
Telegram-бот для дайджеста новых заметок и просмотра хранилища.
Использует aiogram 3.x, асинхронный.
"""

import os
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

from obsidian_mcp import (
    list_files_in_vault,
    get_file_mtime,
    get_file_contents,
    append_to_daily_note
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в переменных окружения")

CHAT_ID = os.getenv("CHAT_ID")
if not CHAT_ID:
    raise ValueError("CHAT_ID не задан в переменных окружения")

VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "/vault")
os.environ["OBSIDIAN_VAULT_PATH"] = VAULT_PATH

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "3600"))
STATE_FILE = os.getenv("STATE_FILE", "/app/state/last_run.txt")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def load_last_run() -> float:
    try:
        with open(STATE_FILE, "r") as f:
            return float(f.read().strip())
    except (FileNotFoundError, ValueError):
        return datetime.now().timestamp()

def save_last_run(timestamp: float):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        f.write(str(timestamp))

async def check_new_notes() -> list:
    files = list_files_in_vault()
    if not files:
        return []

    last_run = load_last_run()
    new_files = []
    for filepath in files:
        mtime = get_file_mtime(filepath)
        if mtime > last_run:
            content = get_file_contents(filepath)
            title = "Без заголовка"
            for line in content.splitlines():
                if line.startswith("#"):
                    title = line.lstrip("#").strip()
                    break
            new_files.append({
                "file": filepath,
                "title": title,
                "mtime": mtime,
                "preview": content[:200] + "..." if len(content) > 200 else content
            })
    return new_files

async def send_digest(new_files: list):
    if not new_files:
        return

    new_files.sort(key=lambda x: x["mtime"], reverse=True)

    message = f"📝 *Дайджест новых заметок* ({len(new_files)})\n\n"
    for idx, note in enumerate(new_files, 1):
        dt = datetime.fromtimestamp(note["mtime"], tz=timezone.utc).astimezone()
        time_str = dt.strftime("%d.%m.%Y %H:%M")
        message += f"{idx}. *{note['title']}*\n"
        message += f"   📄 `{note['file']}`\n"
        message += f"   🕒 {time_str}\n"
        if note["preview"]:
            preview_short = note["preview"].replace("\n", " ").strip()
            if len(preview_short) > 80:
                preview_short = preview_short[:80] + "..."
            message += f"   📖 {preview_short}\n"
        message += "\n"

    if len(message) > 4096:
        message = message[:4000] + "\n... (сообщение обрезано)"

    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        logger.info(f"Дайджест отправлен в чат {CHAT_ID}")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")

async def periodic_check():
    logger.info(f"Запущен бот-дайджест. Интервал: {CHECK_INTERVAL} сек. Хранилище: {VAULT_PATH}")
    while True:
        try:
            new_notes = await check_new_notes()
            if new_notes:
                await send_digest(new_notes)
            save_last_run(datetime.now().timestamp())
        except Exception as e:
            logger.error(f"Ошибка в цикле проверки: {e}")
        await asyncio.sleep(CHECK_INTERVAL)

# ---------- Команды бота ----------

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("👋 Привет! Я бот-дайджест заметок. Буду присылать уведомления о новых или изменённых файлах в вашем хранилище Obsidian.\n\nИспользуйте /help для списка команд.")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🤖 *Доступные команды:*\n"
        "/start – приветствие\n"
        "/help – эта справка\n"
        "/ping – проверка работы бота\n"
        "/add <текст> – добавить заметку в ежедневный файл\n"
        "/list – показать список всех заметок (только имена)\n"
        "/show <имя_файла> – показать содержимое заметки (например, /show README.md)\n"
        "/show без аргументов – то же, что /list"
    )

@dp.message(Command("ping"))
async def cmd_ping(message: types.Message):
    await message.answer("🏓 Pong! Бот работает.")

@dp.message(Command("add"))
async def cmd_add(message: types.Message):
    text = message.text.replace("/add", "").strip()
    if not text:
        await message.answer("❌ Напишите текст заметки после команды, например:\n/add Моя новая заметка")
        return
    try:
        success = append_to_daily_note(text)
        if success:
            await message.answer("✅ Заметка успешно добавлена в ежедневный файл!")
        else:
            await message.answer("❌ Не удалось добавить заметку. Проверьте права доступа к хранилищу.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    """Показывает список всех заметок (только имена файлов и заголовки)"""
    try:
        files = list_files_in_vault()
        if not files:
            await message.answer("📭 В хранилище нет заметок.")
            return

        lines = []
        for filepath in files:
            content = get_file_contents(filepath)
            title = "Без заголовка"
            for line in content.splitlines():
                if line.startswith("#"):
                    title = line.lstrip("#").strip()
                    break
            lines.append(f"📄 `{filepath}` — *{title}*")
        
        if len(lines) > 20:
            part = "\n".join(lines[:20])
            await message.answer(f"📋 *Список заметок (первые 20 из {len(lines)})*\n\n{part}")
        else:
            await message.answer(f"📋 *Список всех заметок ({len(lines)})*\n\n" + "\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении списка: {e}")

@dp.message(Command("show"))
async def cmd_show(message: types.Message):
    """
    Показывает содержимое заметки.
    Если аргумент не указан – выводит список.
    Если указан – ищет файл с таким именем (точное совпадение или частичное).
    """
    args = message.text.replace("/show", "").strip()
    
    if not args:
        await cmd_list(message)
        return

    try:
        files = list_files_in_vault()
        target = args
        if not target.endswith(".md"):
            target += ".md"
        
        found = None
        for f in files:
            if f == target or f.endswith(target) or target in f:
                found = f
                break
        
        if not found:
            await message.answer(f"❌ Заметка «{args}» не найдена. Используйте /list для просмотра всех.")
            return
        
        content = get_file_contents(found)
        if not content.strip():
            await message.answer(f"📄 Заметка `{found}` пуста.")
            return
        
        if len(content) > 4000:
            content = content[:4000] + "\n... (содержимое обрезано)"
        
        await message.answer(f"📄 *{found}*\n\n{content}", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка при чтении заметки: {e}")

async def main():
    asyncio.create_task(periodic_check())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())