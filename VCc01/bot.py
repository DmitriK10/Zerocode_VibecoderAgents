import telebot
from telebot.types import Message
from telebot import apihelper
from config import Config
from database import PostgreSQLStorage
from excel_backup import ExcelBackup
from sqlite_backup import SQLiteBackup

# ---- ПРИНУДИТЕЛЬНОЕ ОТКЛЮЧЕНИЕ SSL (только для отладки) ----
import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

class InsecureHTTPAdapter(HTTPAdapter):
    """Адаптер, который игнорирует ошибки SSL-сертификатов."""
    def init_poolmanager(self, *args, **kwargs):
        # Создаём SSL-контекст без проверки
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super().proxy_manager_for(*args, **kwargs)

# Создаём глобальную сессию с адаптером
session = requests.Session()
session.mount('https://', InsecureHTTPAdapter())
# Отключаем предупреждения
requests.packages.urllib3.disable_warnings()

# Устанавливаем эту сессию для всех запросов бота
apihelper.session = session

# Также переопределяем сессию в модуле requests (для уверенности)
import telebot.apihelper
telebot.apihelper._session = session

class TelegramBot:
    def __init__(self):
        self.bot = telebot.TeleBot(Config.BOT_TOKEN)

        self.db_storage = PostgreSQLStorage()
        self.excel_backup = ExcelBackup()
        self.sqlite_backup = SQLiteBackup()
        self._register_handlers()

    def _register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start_handler(message: Message):
            self.bot.reply_to(message, "Привет! Я бот для сбора анкет.\n"
                                       "Напиши /survey, чтобы начать опрос.\n"
                                       "Напиши /show_data, чтобы увидеть последние 5 опросов.\n"                                       
                                       "Или /backup_status для проверки.")

        @self.bot.message_handler(commands=['survey'])
        def survey_handler(message: Message):
            chat_id = message.chat.id
            self.bot.send_message(chat_id, "1. Как тебя зовут? (Введи ФИО)")
            self.bot.register_next_step_handler(message, self.get_full_name)

        @self.bot.message_handler(commands=['backup_status'])
        def backup_status_handler(message: Message):
            self.bot.reply_to(message, "✅ Резервное копирование активно:\n"
                                       "- PostgreSQL (основная БД)\n"
                                       "- Excel (локальный бэкап)\n"
                                       "- SQLite3 (встроенная БД)")

        @self.bot.message_handler(commands=['show_data'])
        def show_data_handler(message: Message):
            try:
                conn = self.db_storage._get_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, full_name, summ, birthday 
                        FROM public.users 
                        ORDER BY id DESC 
                        LIMIT 5;
                    """)
                    rows = cur.fetchall()
                conn.close()

                if rows:
                    text = "📋 Последние 5 записей из PostgreSQL:\n\n"
                    for row in rows:
                        text += f"ID: {row[0]}, Имя: {row[1]}, Сумма: {row[2]}, Дата: {row[3]}\n"
                else:
                    text = "В базе данных пока нет записей."

                self.bot.reply_to(message, text)

            except Exception as e:
                self.bot.reply_to(message, f"❌ Ошибка при получении данных: {e}")

    def get_full_name(self, message: Message):
        chat_id = message.chat.id
        full_name = message.text.strip()
        if not full_name:
            self.bot.send_message(chat_id, "Имя не может быть пустым. Попробуй ещё раз.")
            self.bot.register_next_step_handler(message, self.get_full_name)
            return
        if not hasattr(self, 'user_data'):
            self.user_data = {}
        self.user_data[chat_id] = {'full_name': full_name}
        self.bot.send_message(chat_id, "2. Какая дата рождения? (в формате 01.01.2001)")
        self.bot.register_next_step_handler(message, self.get_birthday)

    def get_birthday(self, message: Message):
        chat_id = message.chat.id
        birthday = message.text.strip()
        try:
            from datetime import datetime
            datetime.strptime(birthday, "%d.%m.%Y")
        except ValueError:
            self.bot.send_message(chat_id, "Неверный формат. Используй ДД.ММ.ГГГГ")
            self.bot.register_next_step_handler(message, self.get_birthday)
            return

        full_name = self.user_data.get(chat_id, {}).get('full_name')
        if not full_name:
            self.bot.send_message(chat_id, "Что-то пошло не так, начни заново /survey")
            return

        success = True
        if not self.db_storage.save_user_data(full_name, birthday):
            success = False
        if not self.excel_backup.save_user_data(full_name, birthday):
            success = False
        if not self.sqlite_backup.save_user_data(full_name, birthday):
            success = False

        if success:
            self.bot.send_message(chat_id, "✅ Анкета сохранена! Спасибо.")
        else:
            self.bot.send_message(chat_id, "⚠️ Произошла ошибка при сохранении. Обратитесь к администратору.")

        if hasattr(self, 'user_data'):
            self.user_data.pop(chat_id, None)

    def run(self):
        print("🚀 Бот запущен...")
        self.bot.infinity_polling()

if __name__ == "__main__":
    bot_app = TelegramBot()
    bot_app.run()