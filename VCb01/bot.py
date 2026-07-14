import logging
import os
from dotenv import load_dotenv
import telebot
from telebot import types
from openai import OpenAI

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.proxyapi.ru/openai/v1')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

if not BOT_TOKEN or not OPENAI_API_KEY:
    raise ValueError("Не заданы обязательные переменные: BOT_TOKEN, OPENAI_API_KEY")

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

# --- Класс для работы с AI (SOLID: Single Responsibility) ---
class AIClient:
    """Отвечает за взаимодействие с LLM через ProxyAPI."""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.system_prompt = (
            "Ты вежливый и профессиональный личный помощник, работающий в Telegram. "
            "Отвечай кратко, но содержательно. Если не знаешь ответа, честно скажи об этом."
        )

    def get_response(self, user_message: str) -> str:
        """
        Отправляет сообщение пользователя в модель и возвращает ответ.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1024
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Ошибка при вызове OpenAI: {e}")
            return "Извините, произошла ошибка при обработке запроса. Попробуйте позже."

# --- Инициализация бота и AI-клиента ---
bot = telebot.TeleBot(BOT_TOKEN)
ai_client = AIClient(OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL)

# --- Обработчики команд ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Приветственное сообщение с описанием возможностей."""
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn = types.KeyboardButton("Задать вопрос")
    markup.add(btn)
    bot.send_message(
        message.chat.id,
        "🤖 Привет! Я ваш личный ИИ-помощник.\n\n"
        "Просто напишите мне любой вопрос, и я постараюсь на него ответить.\n"
        "Я использую модель GPT-4o-mini через ProxyAPI.\n\n"
        "Нажмите кнопку 'Задать вопрос' или просто введите текст.",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "Задать вопрос")
def ask_question_prompt(message):
    """Ответ на кнопку 'Задать вопрос'."""
    bot.send_message(message.chat.id, "Напишите ваш вопрос:")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    """
    Обрабатывает все текстовые сообщения и отправляет их в AI.
    """
    logger.info(f"Пользователь {message.from_user.id}: {message.text}")
    # Отправляем индикатор набора текста
    bot.send_chat_action(message.chat.id, action='typing')

    # Получаем ответ от AI
    reply = ai_client.get_response(message.text)

    # Отправляем ответ пользователю
    bot.reply_to(message, reply)
    logger.info(f"Ответ AI для {message.from_user.id}: {reply[:50]}...")

# --- Запуск бота ---
if __name__ == "__main__":
    logger.info("Бот запущен...")
    bot.polling(none_stop=True)