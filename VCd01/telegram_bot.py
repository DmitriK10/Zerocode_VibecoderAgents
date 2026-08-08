# telegram_bot.py
import asyncio
import os
import logging
from pathlib import Path
from typing import Optional, Callable, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, error as tg_error
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.request import HTTPXRequest
from dotenv import load_dotenv

from agents_runner import run_ai_history, run_seo_analysis, run_custom_task

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Вспомогательная функция для получения message_target ---
def get_message_target(target):
    """Извлекает объект сообщения из Update или CallbackQuery."""
    if hasattr(target, 'effective_message'):
        return target.effective_message
    elif hasattr(target, 'message'):
        return target.message
    else:
        raise ValueError("Неизвестный тип target")

# --- Глобальный обработчик ошибок с логированием ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if isinstance(context.error, tg_error.NetworkError):
        logger.warning(f"Network error occurred: {context.error}. The bot will continue.")
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text("⚠️ Сетевая ошибка, попробуйте позже.")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")
        return
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("❌ Произошла внутренняя ошибка.")
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

# --- Безопасная отправка сообщения ---
async def safe_send_message(target, text: str, reply_markup=None):
    try:
        message_target = get_message_target(target)
    except ValueError as e:
        logger.error(str(e))
        return

    for attempt in range(3):
        try:
            await message_target.reply_text(text, reply_markup=reply_markup)
            return
        except tg_error.NetworkError as e:
            logger.warning(f"Network error on send attempt {attempt+1}: {e}")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return

# --- Отправка результата ---
async def send_result(target, result: str, filename: str, caption: str = "📄 Результат", reply_markup=None):
    try:
        message_target = get_message_target(target)
    except ValueError as e:
        logger.error(str(e))
        return

    try:
        if len(result) > 4096:
            output_path = Path(__file__).parent / filename
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result)
            for attempt in range(3):
                try:
                    with open(output_path, "rb") as f:
                        await message_target.reply_document(
                            document=f,
                            filename=filename,
                            caption=caption
                        )
                    break
                except tg_error.NetworkError:
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Failed to send document: {e}")
                    break
        else:
            await safe_send_message(target, result)
        if reply_markup:
            await safe_send_message(target, "✅ Готово! Выберите другую задачу:", reply_markup)
    except Exception as e:
        logger.error(f"Error in send_result: {e}")

# --- Универсальный запуск задачи ---
async def run_task(target, task_func: Callable, args: tuple, start_msg: str, filename: str, caption: str, reply_markup):
    try:
        message_target = get_message_target(target)
    except ValueError as e:
        logger.error(str(e))
        return

    await message_target.reply_text(start_msg)
    result = await asyncio.to_thread(task_func, *args)
    await send_result(target, result, filename, caption, reply_markup)

# --- Клавиатура ---
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📜 История ИИ (быстро)", callback_data="history")],
        [InlineKeyboardButton("🔎 История ИИ (с проверкой)", callback_data="history_factcheck")],
        [InlineKeyboardButton("🔍 SEO-анализ сайта", callback_data="seo")],
        [InlineKeyboardButton("✍️ Произвольная задача", callback_data="custom")],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- Обработчики ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я интеллектуальный бот-агент на базе CrewAI.\n"
        "Выберите задачу из меню ниже:",
        reply_markup=main_menu_keyboard()
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите задачу:", reply_markup=main_menu_keyboard())

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🛑 Текущая задача отменена. Вы можете выбрать новую.",
        reply_markup=main_menu_keyboard()
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if context.user_data.get('task_running'):
        await query.edit_message_text("⏳ Уже выполняется задача. Дождитесь завершения или используйте /cancel.")
        return

    try:
        if data == "history":
            context.user_data['task_running'] = True
            await run_task(query, run_ai_history, (False,),
                           "⏳ Запускаю обзор истории ИИ (быстрый режим)...",
                           "ai_history_review.md", "📄 Обзор истории ИИ (быстрый)", main_menu_keyboard())
            context.user_data.pop('task_running', None)

        elif data == "history_factcheck":
            context.user_data['task_running'] = True
            await run_task(query, run_ai_history, (True,),
                           "⏳ Запускаю обзор истории ИИ с фактчекером... (3-5 мин)",
                           "ai_history_review_factchecked.md", "📄 Обзор истории ИИ (с проверкой)", main_menu_keyboard())
            context.user_data.pop('task_running', None)

        elif data == "seo":
            await query.edit_message_text("🔗 Введите URL сайта для SEO-анализа (например, https://example.com):")
            context.user_data['task_type'] = 'seo'

        elif data == "custom":
            await query.edit_message_text("✍️ Опишите вашу задачу подробно (например, 'Сравни технологии GPT-4 и Gemini'):")
            context.user_data['task_type'] = 'custom'

        else:
            await query.edit_message_text("Неизвестная команда. Выберите задачу из меню:", reply_markup=main_menu_keyboard())
    except Exception as e:
        context.user_data.pop('task_running', None)
        logger.error(f"Error in button_callback: {e}")
        await safe_send_message(query, f"❌ Ошибка: {str(e)}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    task_type = context.user_data.get('task_type')

    if context.user_data.get('task_running'):
        await update.message.reply_text("⏳ Уже выполняется задача. Дождитесь завершения или используйте /cancel.")
        return

    try:
        if task_type == 'seo':
            context.user_data['task_running'] = True
            await run_task(update, run_seo_analysis, (text,),
                           "⏳ Запускаю SEO-анализ... (до минуты)",
                           "seo_result.txt", "📄 SEO-анализ", main_menu_keyboard())
            context.user_data.pop('task_running', None)
            context.user_data.pop('task_type', None)

        elif task_type == 'custom':
            context.user_data['task_running'] = True
            await run_task(update, run_custom_task, (text,),
                           "⏳ Обрабатываю вашу задачу...",
                           "custom_result.txt", "📄 Результат", main_menu_keyboard())
            context.user_data.pop('task_running', None)
            context.user_data.pop('task_type', None)

        else:
            await update.message.reply_text("Сначала выберите задачу из меню:", reply_markup=main_menu_keyboard())
    except Exception as e:
        context.user_data.pop('task_running', None)
        logger.error(f"Error in handle_text: {e}")
        await safe_send_message(update, f"❌ Ошибка: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Бот-агент на CrewAI.\n\n"
        "Доступные команды:\n"
        "/start - начать\n"
        "/menu - показать меню\n"
        "/cancel - отменить текущую задачу\n"
        "/help - справка\n\n"
        "Вы можете выбрать задачу из меню или отправить текст для произвольной задачи."
    )

# --- Главная функция ---
def main():
    # Увеличенные таймауты
    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=20.0,
    )

    application = Application.builder().token(BOT_TOKEN).request(request).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_error_handler(error_handler)

    print("🤖 Бот запущен. Нажмите Ctrl+C для остановки.")
    application.run_polling(allowed_updates=Update.ALL_TYPES, bootstrap_retries=5)

if __name__ == "__main__":
    main()