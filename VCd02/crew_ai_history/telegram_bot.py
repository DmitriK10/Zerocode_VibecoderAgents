# telegram_bot.py
import asyncio
import logging
import hashlib
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, error as tg_error
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.request import HTTPXRequest

from config import settings
from logger import logger
from task_service import task_service

# Настройка логгера для библиотеки telegram
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


# ---------- Вспомогательные функции ----------
def get_message_target(target):
    """Извлекает объект сообщения из Update или CallbackQuery."""
    if hasattr(target, 'effective_message'):
        return target.effective_message
    elif hasattr(target, 'message'):
        return target.message
    else:
        raise ValueError("Неизвестный тип target")


async def safe_send_message(target, text: str, reply_markup=None):
    try:
        msg_target = get_message_target(target)
    except ValueError as e:
        logger.error(str(e))
        return

    for attempt in range(3):
        try:
            await msg_target.reply_text(text, reply_markup=reply_markup)
            return
        except tg_error.NetworkError as e:
            logger.warning(f"Сетевая ошибка при отправке (попытка {attempt+1}): {e}")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            return


async def send_result(target, result: str, filename: str, caption: str = "📄 Результат", reply_markup=None):
    try:
        msg_target = get_message_target(target)
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
                        await msg_target.reply_document(
                            document=f,
                            filename=filename,
                            caption=caption
                        )
                    break
                except tg_error.NetworkError:
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Ошибка отправки документа: {e}")
                    break
        else:
            await safe_send_message(target, result)
        if reply_markup:
            await safe_send_message(target, "✅ Готово! Выберите другую задачу:", reply_markup)
    except Exception as e:
        logger.error(f"Ошибка в send_result: {e}")


# ---------- Клавиатура ----------
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📜 История ИИ (быстро)", callback_data="history")],
        [InlineKeyboardButton("🔎 История ИИ (с проверкой)", callback_data="history_factcheck")],
        [InlineKeyboardButton("🔍 SEO-анализ сайта", callback_data="seo")],
        [InlineKeyboardButton("✍️ Произвольная задача", callback_data="custom")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ---------- Обработчики ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я интеллектуальный бот-агент на базе CrewAI.\n"
        "Выберите задачу из меню ниже:",
        reply_markup=main_menu_keyboard()
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите задачу:", reply_markup=main_menu_keyboard())


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет текущую задачу пользователя."""
    task_id = context.user_data.get("current_task_id")
    if task_id:
        cancelled = task_service.cancel_task(task_id)
        if cancelled:
            await update.message.reply_text("🛑 Текущая задача отменена.")
        else:
            await update.message.reply_text("⚠️ Задача уже завершена или не найдена.")
    else:
        await update.message.reply_text("❌ Нет активной задачи для отмены.")
    context.user_data.clear()
    await update.message.reply_text(
        "Вы можете выбрать новую задачу.",
        reply_markup=main_menu_keyboard()
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # Проверяем, не выполняется ли уже задача
    if context.user_data.get("task_running"):
        await query.edit_message_text("⏳ Уже выполняется задача. Дождитесь завершения или используйте /cancel.")
        return

    try:
        if data == "history":
            context.user_data["task_running"] = True
            await query.edit_message_text("⏳ Запускаю обзор истории ИИ (быстрый режим)...")
            try:
                # Генерируем ID задачи и сохраняем для возможности отмены
                task_id = task_service.generate_task_id("ai_history", False)
                context.user_data["current_task_id"] = task_id

                result = await task_service.run_task("ai_history", False)
                await send_result(query, result, "ai_history_review.md", "📄 Обзор истории ИИ (быстрый)", main_menu_keyboard())
            except Exception as e:
                logger.error(f"Ошибка в history: {e}")
                await safe_send_message(query, f"❌ Ошибка: {str(e)}")
            finally:
                context.user_data.pop("task_running", None)
                context.user_data.pop("current_task_id", None)

        elif data == "history_factcheck":
            context.user_data["task_running"] = True
            await query.edit_message_text("⏳ Запускаю обзор истории ИИ с фактчекером... (3-5 мин)")
            try:
                # Генерируем ID задачи и сохраняем для возможности отмены
                task_id = task_service.generate_task_id("ai_history", True)
                context.user_data["current_task_id"] = task_id

                result = await task_service.run_task("ai_history", True)
                await send_result(query, result, "ai_history_review_factchecked.md", "📄 Обзор истории ИИ (с проверкой)", main_menu_keyboard())
            except Exception as e:
                logger.error(f"Ошибка в history_factcheck: {e}")
                await safe_send_message(query, f"❌ Ошибка: {str(e)}")
            finally:
                context.user_data.pop("task_running", None)
                context.user_data.pop("current_task_id", None)

        elif data == "seo":
            await query.edit_message_text("🔗 Введите URL сайта для SEO-анализа (например, https://example.com):")
            context.user_data["task_type"] = "seo"

        elif data == "custom":
            await query.edit_message_text("✍️ Опишите вашу задачу подробно (например, 'Сравни технологии GPT-4 и Gemini'):")
            context.user_data["task_type"] = "custom"

        else:
            await query.edit_message_text("Неизвестная команда.", reply_markup=main_menu_keyboard())
    except Exception as e:
        context.user_data.pop("task_running", None)
        logger.error(f"Ошибка в button_callback: {e}")
        await safe_send_message(query, f"❌ Ошибка: {str(e)}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    task_type = context.user_data.get("task_type")

    if context.user_data.get("task_running"):
        await update.message.reply_text("⏳ Уже выполняется задача. Дождитесь завершения или используйте /cancel.")
        return

    try:
        if task_type == "seo":
            # Валидация URL
            import urllib.parse
            parsed = urllib.parse.urlparse(text)
            if not parsed.scheme or not parsed.netloc:
                await update.message.reply_text("❌ Некорректный URL. Попробуйте снова.")
                return

            context.user_data["task_running"] = True
            await update.message.reply_text("⏳ Запускаю SEO-анализ... (до минуты)")
            try:
                # Генерируем ID задачи и сохраняем для возможности отмены
                task_id = task_service.generate_task_id("seo", text)
                context.user_data["current_task_id"] = task_id

                result = await task_service.run_task("seo", text)
                await send_result(update, result, "seo_result.txt", "📄 SEO-анализ", main_menu_keyboard())
            except Exception as e:
                logger.error(f"Ошибка в SEO: {e}")
                await safe_send_message(update, f"❌ Ошибка: {str(e)}")
            finally:
                context.user_data.pop("task_running", None)
                context.user_data.pop("task_type", None)
                context.user_data.pop("current_task_id", None)

        elif task_type == "custom":
            # Ограничение длины
            if len(text) > settings.max_custom_query_length:
                await update.message.reply_text(f"❌ Запрос слишком длинный (макс. {settings.max_custom_query_length} символов).")
                return

            context.user_data["task_running"] = True
            await update.message.reply_text("⏳ Обрабатываю вашу задачу...")
            try:
                # Генерируем ID задачи и сохраняем для возможности отмены
                task_id = task_service.generate_task_id("custom", text)
                context.user_data["current_task_id"] = task_id

                result = await task_service.run_task("custom", text)
                await send_result(update, result, "custom_result.txt", "📄 Результат", main_menu_keyboard())
            except Exception as e:
                logger.error(f"Ошибка в custom: {e}")
                await safe_send_message(update, f"❌ Ошибка: {str(e)}")
            finally:
                context.user_data.pop("task_running", None)
                context.user_data.pop("task_type", None)
                context.user_data.pop("current_task_id", None)

        else:
            await update.message.reply_text("Сначала выберите задачу из меню:", reply_markup=main_menu_keyboard())
    except Exception as e:
        context.user_data.pop("task_running", None)
        logger.error(f"Ошибка в handle_text: {e}")
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


# ---------- Обработчик ошибок ----------
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Исключение при обработке обновления:", exc_info=context.error)
    if isinstance(context.error, tg_error.NetworkError):
        logger.warning(f"Сетевая ошибка: {context.error}")
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text("⚠️ Сетевая ошибка, попробуйте позже.")
        except Exception:
            pass
        return
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("❌ Произошла внутренняя ошибка.")
    except Exception:
        pass


# ---------- Главная функция ----------
def main():
    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=20.0,
    )

    application = Application.builder().token(settings.bot_token).request(request).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_error_handler(error_handler)

    logger.info("🤖 Бот запущен. Нажмите Ctrl+C для остановки.")
    application.run_polling(allowed_updates=Update.ALL_TYPES, bootstrap_retries=5)


if __name__ == "__main__":
    main()