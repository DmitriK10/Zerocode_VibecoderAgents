# tests/test_telegram_bot.py
import pytest
from telegram import Update, User
from telegram.ext import ContextTypes
from unittest.mock import AsyncMock, MagicMock

from telegram_bot import start, cancel


@pytest.fixture
def update():
    update = MagicMock(spec=Update)
    update.effective_user = User(id=123, first_name="Test", is_bot=False)
    # Создаём объект message как AsyncMock
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()
    # Если где-то используется effective_message, приравниваем его к message
    update.effective_message = update.message
    return update


@pytest.fixture
def context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    return context


@pytest.mark.asyncio
async def test_start(update, context):
    await start(update, context)
    update.message.reply_text.assert_called_once()
    args, _ = update.message.reply_text.call_args
    assert "Выберите задачу" in args[0]


@pytest.mark.asyncio
async def test_cancel_no_task(update, context):
    # В context.user_data нет current_task_id, поэтому cancel вернёт сообщение об отсутствии задачи
    await cancel(update, context)
    # Проверяем, что было отправлено сообщение "❌ Нет активной задачи для отмены."
    update.message.reply_text.assert_any_call("❌ Нет активной задачи для отмены.")