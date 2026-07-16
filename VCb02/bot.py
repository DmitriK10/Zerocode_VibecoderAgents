"""
Telegram-бот с поддержкой двух российских LLM:
- GigaChat (Сбер)
- YandexGPT (Яндекс.Облако)

Пользователь выбирает модель через inline-клавиатуру.
"""

import logging
import os
import time
from dotenv import load_dotenv
import telebot
from telebot import types
import requests
from gigachat import GigaChat
from telebot.apihelper import ApiTelegramException

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
GIGACHAT_AUTH_KEY = os.getenv('GIGACHAT_AUTH_KEY')
YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан")
if not GIGACHAT_AUTH_KEY:
    raise ValueError("GIGACHAT_AUTH_KEY не задан")
if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
    raise ValueError("YANDEX_API_KEY и YANDEX_FOLDER_ID должны быть заданы")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Модели (клиенты) ---

class GigaChatClient:
    """
    Клиент для GigaChat (Сбер).
    Использует официальную библиотеку gigachat.
    """
    def __init__(self, auth_key: str):
        self.auth_key = auth_key
        self.client = GigaChat(auth=self.auth_key, verify_ssl_certs=False)

    def generate(self, prompt: str) -> str:
        """Отправляет запрос и возвращает ответ модели."""
        try:
            response = self.client.chat(prompt)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"GigaChat ошибка: {e}")
            return "⚠️ Ошибка при обращении к GigaChat. Попробуйте позже."


class YandexGPTClient:
    """
    Клиент для YandexGPT через REST API.
    Использует API-ключ и folder_id.
    """
    def __init__(self, api_key: str, folder_id: str):
        self.api_key = api_key
        self.folder_id = folder_id
        self.url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    def generate(self, prompt: str) -> str:
        """Отправляет запрос и возвращает ответ модели."""
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": 2000
            },
            "messages": [
                {"role": "user", "text": prompt}
            ]
        }
        # Увеличиваем таймаут до 60 секунд и делаем повторную попытку
        for attempt in range(2):
            try:
                resp = requests.post(self.url, headers=headers, json=data, timeout=60)
                resp.raise_for_status()
                result = resp.json()
                return result['result']['alternatives'][0]['message']['text']
            except requests.exceptions.Timeout:
                logger.error(f"YandexGPT таймаут (попытка {attempt+1})")
                if attempt == 0:
                    time.sleep(2)  # пауза перед повторной попыткой
                    continue
                else:
                    return "⏳ Сервер YandexGPT не отвечает. Попробуйте позже."
            except requests.exceptions.RequestException as e:
                logger.error(f"YandexGPT ошибка запроса: {e}")
                return "⚠️ Ошибка при обращении к YandexGPT. Проверьте интернет или API-ключ."
            except (KeyError, IndexError) as e:
                logger.error(f"YandexGPT ошибка в ответе: {e}")
                return "⚠️ Неожиданный формат ответа от YandexGPT."
        return "⚠️ Не удалось получить ответ от YandexGPT."


# --- Инициализация бота и клиентов ---

bot = telebot.TeleBot(BOT_TOKEN)
giga_client = GigaChatClient(GIGACHAT_AUTH_KEY)
yandex_client = YandexGPTClient(YANDEX_API_KEY, YANDEX_FOLDER_ID)

# Храним выбранную модель для каждого пользователя (в памяти)
user_model = {}  # {chat_id: 'giga' or 'yandex'}

# Модели для отображения
MODEL_NAMES = {
    'giga': '🧠 GigaChat (Сбер)',
    'yandex': '🧠 YandexGPT (Яндекс)'
}

# --- Клавиатуры ---

def get_model_selection_keyboard():
    """Возвращает inline-клавиатуру для выбора модели."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_giga = types.InlineKeyboardButton("GigaChat", callback_data="model_giga")
    btn_yandex = types.InlineKeyboardButton("YandexGPT", callback_data="model_yandex")
    markup.add(btn_giga, btn_yandex)
    return markup

# --- Обработчики команд ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Приветствие и предложение выбрать модель."""
    chat_id = message.chat.id
    # Устанавливаем модель по умолчанию (GigaChat)
    user_model[chat_id] = 'giga'
    bot.send_message(
        chat_id,
        f"🤖 Привет! Я умею отвечать на вопросы с помощью двух нейросетей:\n"
        f"- {MODEL_NAMES['giga']}\n"
        f"- {MODEL_NAMES['yandex']}\n\n"
        f"Сейчас выбрана: {MODEL_NAMES[user_model[chat_id]]}\n"
        f"Чтобы сменить модель, используй кнопки ниже.",
        reply_markup=get_model_selection_keyboard()
    )

@bot.message_handler(commands=['switch'])
def switch_model(message):
    """Команда для смены модели (вызывает ту же клавиатуру)."""
    bot.send_message(
        message.chat.id,
        "Выберите модель для ответа:",
        reply_markup=get_model_selection_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('model_'))
def callback_model_choice(call):
    """Обрабатывает выбор модели через inline-кнопки."""
    chat_id = call.message.chat.id
    model = call.data.split('_')[1]  # 'giga' или 'yandex'
    old_model = user_model.get(chat_id)
    user_model[chat_id] = model
    bot.answer_callback_query(call.id, f"Выбрана модель: {MODEL_NAMES[model]}")

    # Если модель не изменилась — не редактируем сообщение, чтобы избежать ошибки
    if old_model == model:
        return

    try:
        bot.edit_message_text(
            f"✅ Модель изменена на: {MODEL_NAMES[model]}\n"
            f"Теперь задайте мне любой вопрос.",
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=get_model_selection_keyboard()
        )
    except ApiTelegramException as e:
        if "message is not modified" in str(e):
            # Игнорируем эту ошибку
            logger.info(f"Попытка редактирования без изменений (пользователь {chat_id})")
        else:
            logger.error(f"Ошибка редактирования сообщения: {e}")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    """Обрабатывает все текстовые сообщения (кроме команд)."""
    chat_id = message.chat.id
    text = message.text.strip()
    if not text:
        return

    # Определяем, какая модель выбрана у пользователя
    model_key = user_model.get(chat_id, 'giga')  # по умолчанию GigaChat
    model_name = MODEL_NAMES[model_key]
    logger.info(f"Пользователь {chat_id} ({model_name}): {text}")

    # Отправляем индикатор набора текста
    bot.send_chat_action(chat_id, action='typing')

    # Получаем ответ от выбранной модели
    if model_key == 'giga':
        reply = giga_client.generate(text)
    else:  # yandex
        reply = yandex_client.generate(text)

    # Отправляем ответ
    bot.reply_to(message, f"*{model_name}*\n{reply}", parse_mode='Markdown')

# --- Запуск бота ---

if __name__ == "__main__":
    logger.info("Бот запущен...")
    bot.polling(none_stop=True)