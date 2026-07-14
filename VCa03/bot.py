import logging
import sqlite3
import os
import re
import time
from datetime import datetime
from io import BytesIO

import requests
import telebot
from telebot import types
from dotenv import load_dotenv

# Загружаем токен из .env
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("Токен не найден. Создайте файл .env с BOT_TOKEN=ваш_токен")

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

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# --- Работа с базой данных ---
DB_NAME = 'recipes.db'

def init_db():
    """Создаёт таблицу избранных рецептов, если её нет."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            recipe_id TEXT,
            recipe_name TEXT,
            recipe_thumb TEXT,
            recipe_instructions TEXT,
            recipe_youtube TEXT,
            ingredients TEXT,
            rating INTEGER DEFAULT 0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, recipe_id)
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")

def add_favorite(user_id, recipe_data, rating=0):
    """Добавляет рецепт в избранное с указанным рейтингом."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO favorites 
        (user_id, recipe_id, recipe_name, recipe_thumb, recipe_instructions, recipe_youtube, ingredients, rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        recipe_data['idMeal'],
        recipe_data['strMeal'],
        recipe_data['strMealThumb'],
        recipe_data.get('strInstructions', ''),
        recipe_data.get('strYoutube', ''),
        ', '.join([f"{recipe_data[f'strIngredient{i}']} - {recipe_data[f'strMeasure{i}']}" 
                   for i in range(1, 21) if recipe_data.get(f'strIngredient{i}')]),
        rating
    ))
    conn.commit()
    conn.close()
    logger.info(f"Пользователь {user_id} добавил рецепт {recipe_data['idMeal']} с рейтингом {rating}")

def get_favorites(user_id):
    """Возвращает список избранных рецептов для пользователя, отсортированных по убыванию рейтинга."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT recipe_id, recipe_name, recipe_thumb, recipe_instructions, recipe_youtube, ingredients, rating
        FROM favorites
        WHERE user_id = ?
        ORDER BY rating DESC, added_at DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_favorite(user_id, recipe_id):
    """Удаляет рецепт из избранного."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM favorites WHERE user_id = ? AND recipe_id = ?', (user_id, recipe_id))
    conn.commit()
    conn.close()
    logger.info(f"Пользователь {user_id} удалил рецепт {recipe_id}")

def update_rating(user_id, recipe_id, new_rating):
    """Обновляет рейтинг рецепта."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE favorites SET rating = ? WHERE user_id = ? AND recipe_id = ?', 
                   (new_rating, user_id, recipe_id))
    conn.commit()
    conn.close()
    logger.info(f"Пользователь {user_id} обновил рейтинг рецепта {recipe_id} на {new_rating}")

# --- Улучшенная транслитерация с исключениями для частых слов ---
def transliterate(text):
    """Преобразует кириллицу в латиницу с учётом распространённых исключений."""
    # Словарь исключений (целые слова)
    exceptions = {
        'пицца': 'pizza',
        'курица': 'chicken',
        'суп': 'soup',
        'салат': 'salad',
        'паста': 'pasta',
        'рис': 'rice',
        'картошка': 'potato',
        'говядина': 'beef',
        'свинина': 'pork',
        'рыба': 'fish',
        'омлет': 'omelette',
        'блины': 'pancakes',
        'торт': 'cake',
        'хлеб': 'bread',
    }
    # Проверяем, есть ли точное совпадение (регистронезависимо)
    lower_text = text.lower()
    for ru, en in exceptions.items():
        if lower_text == ru:
            return en
        # Если фраза содержит слово, можно заменить, но пока оставим точное.

    # Общая транслитерация
    cyrillic_to_latin = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z',
        'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    result = []
    for char in lower_text:
        if char.isalpha() and char in cyrillic_to_latin:
            result.append(cyrillic_to_latin[char])
        else:
            result.append(char)
    return ''.join(result)

# --- Функции для работы с API (с повторными попытками) ---
def search_recipe_by_name(query, retries=2):
    """Ищет рецепты по названию. Если запрос на кириллице – транслитерирует."""
    if re.search('[а-яА-Я]', query):
        translit_query = transliterate(query)
        logger.info(f"Транслитерация: {query} -> {translit_query}")
        queries_to_try = [translit_query, query]  # сначала транслит, потом оригинал
    else:
        queries_to_try = [query]

    for q in queries_to_try:
        url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={q}"
        for attempt in range(retries):
            try:
                logger.info(f"Попытка {attempt+1}: запрос к {url}")
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                meals = data.get('meals')
                if meals:
                    logger.info(f"Найдено {len(meals)} рецептов по запросу '{q}'")
                    return meals
                else:
                    logger.info(f"По запросу '{q}' ничего не найдено")
                    break
            except Exception as e:
                logger.error(f"Ошибка запроса (попытка {attempt+1}): {e}")
                if attempt == retries - 1:
                    continue
                time.sleep(1)
    logger.warning(f"Ничего не найдено для запроса '{query}'")
    return None

def get_recipe_by_id(recipe_id):
    """Получает рецепт по ID с повторной попыткой."""
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={recipe_id}"
    for attempt in range(2):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            meals = data.get('meals', [])
            return meals[0] if meals else None
        except Exception as e:
            logger.error(f"Ошибка получения рецепта по ID {recipe_id}: {e}")
            time.sleep(1)
    return None

# --- Обработчики команд ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Приветственное сообщение с меню."""
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("🔍 Поиск рецептов")
    btn2 = types.KeyboardButton("📚 Мои рецепты")
    markup.add(btn1, btn2)
    bot.send_message(
        message.chat.id,
        "🍳 Привет! Я помогу найти рецепты и сохранить любимые.\n\n"
        "🔹 Вводи названия на русском (например, 'пицца', 'курица') или на английском ('pizza', 'chicken').\n"
        "🔹 Используй кнопки ниже:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "🔍 Поиск рецептов")
def handle_search_button(message):
    """Запускает процесс поиска."""
    bot.send_message(message.chat.id, "Введите название блюда (можно на русском или английском):")
    bot.register_next_step_handler(message, process_search_query)

def process_search_query(message):
    """Обрабатывает введённое название и показывает результаты."""
    query = message.text.strip()
    if not query:
        bot.send_message(message.chat.id, "Пожалуйста, введите непустое название.")
        return

    bot.send_message(message.chat.id, f"🔎 Ищу рецепты по запросу «{query}»...")
    meals = search_recipe_by_name(query)

    if meals is None:
        bot.send_message(
            message.chat.id,
            "❌ Не удалось найти рецепты. Проверьте интернет или попробуйте ввести название на английском (например, 'pizza')."
        )
        return
    if not meals:
        bot.send_message(
            message.chat.id,
            "😕 Ничего не найдено. Попробуйте другое название на английском (например, 'chicken', 'pizza')."
        )
        return

    # Отправляем первые 10 найденных рецептов
    for meal in meals[:10]:
        show_recipe_card(message.chat.id, meal)

def show_recipe_card(chat_id, meal):
    """
    Отображает карточку рецепта.
    Фото отправляется с кратким caption (только название),
    а полный текст (ингредиенты, инструкция, видео) отправляется отдельным сообщением,
    чтобы избежать превышения лимита Telegram на длину подписи (1024 символа).
    """
    recipe_id = meal['idMeal']
    name = meal['strMeal']
    thumb_url = meal['strMealThumb']
    instructions = meal.get('strInstructions', 'Инструкция отсутствует.')
    youtube = meal.get('strYoutube', '')

    # Собираем ингредиенты
    ingredients = []
    for i in range(1, 21):
        ing = meal.get(f'strIngredient{i}')
        measure = meal.get(f'strMeasure{i}')
        if ing and ing.strip():
            ingredients.append(f"{measure} {ing}".strip())
    ingredients_text = "\n".join(ingredients) if ingredients else "Ингредиенты не указаны."

    # Формируем полный текст для отдельного сообщения
    full_text = f"<b>{name}</b>\n\n"
    full_text += f"<b>📝 Ингредиенты:</b>\n{ingredients_text}\n\n"
    full_text += f"<b>📖 Инструкция:</b>\n{instructions}\n"
    if youtube:
        full_text += f"\n🎬 <a href='{youtube}'>Видеорецепт на YouTube</a>"

    # Клавиатура для сохранения
    markup = types.InlineKeyboardMarkup(row_width=2)
    save_btn = types.InlineKeyboardButton("⭐ Сохранить в избранное", callback_data=f"save_{recipe_id}")
    markup.add(save_btn)

    # Отправляем фото с кратким заголовком (только название)
    try:
        img_response = requests.get(thumb_url, timeout=10)
        img_response.raise_for_status()
        photo_file = BytesIO(img_response.content)
        photo_file.name = f"{recipe_id}.jpg"
        # Отправляем фото с коротким caption (только название)
        bot.send_photo(chat_id, photo_file, caption=f"<b>{name}</b>", parse_mode='HTML')
    except Exception as e:
        logger.error(f"Ошибка при отправке фото: {e}")
        # Если фото не загрузилось, просто отправляем текст

    # Отправляем полный текст с кнопкой отдельным сообщением
    bot.send_message(chat_id, full_text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('save_'))
def handle_save_callback(call):
    """Обрабатывает нажатие «Сохранить в избранное»."""
    recipe_id = call.data.split('_')[1]
    user_id = call.from_user.id

    meal = get_recipe_by_id(recipe_id)
    if not meal:
        bot.answer_callback_query(call.id, "Рецепт не найден, попробуйте снова.")
        return

    # Предлагаем поставить рейтинг
    markup = types.InlineKeyboardMarkup(row_width=5)
    stars = [
        types.InlineKeyboardButton("⭐", callback_data=f"rate_{recipe_id}_1"),
        types.InlineKeyboardButton("⭐⭐", callback_data=f"rate_{recipe_id}_2"),
        types.InlineKeyboardButton("⭐⭐⭐", callback_data=f"rate_{recipe_id}_3"),
        types.InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"rate_{recipe_id}_4"),
        types.InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"rate_{recipe_id}_5")
    ]
    markup.add(*stars)
    # Убираем клавиатуру у предыдущего сообщения (если она была)
    try:
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
    except:
        pass
    bot.send_message(
        call.message.chat.id,
        "🌟 Оцените рецепт от 1 до 5 звёзд:",
        reply_markup=markup
    )
    bot.answer_callback_query(call.id, "Выберите рейтинг")

@bot.callback_query_handler(func=lambda call: call.data.startswith('rate_'))
def handle_rating_callback(call):
    """Обрабатывает выбор рейтинга и сохраняет рецепт."""
    _, recipe_id, rating_str = call.data.split('_')
    rating = int(rating_str)
    user_id = call.from_user.id

    meal = get_recipe_by_id(recipe_id)
    if not meal:
        bot.answer_callback_query(call.id, "Рецепт не найден.")
        return

    add_favorite(user_id, meal, rating)

    bot.edit_message_text(
        f"✅ Рецепт сохранён с рейтингом {rating} ⭐!",
        call.message.chat.id,
        call.message.message_id
    )
    bot.answer_callback_query(call.id, "Сохранено!")

# --- Команда "Мои рецепты" ---
@bot.message_handler(func=lambda m: m.text == "📚 Мои рецепты")
def handle_my_recipes(message):
    """Показывает список избранных рецептов."""
    user_id = message.from_user.id
    favorites = get_favorites(user_id)

    if not favorites:
        bot.send_message(message.chat.id, "У вас пока нет избранных рецептов. Добавьте их через поиск!")
        return

    for recipe in favorites:
        recipe_id, name, thumb, instructions, youtube, ingredients, rating = recipe
        stars = '⭐' * rating + ('☆' * (5 - rating)) if rating else 'Без оценки'
        text = f"<b>{name}</b>\nРейтинг: {stars}\n\n"
        if ingredients:
            text += f"<b>Ингредиенты:</b>\n{ingredients[:200]}...\n\n"
        text += f"<a href='{thumb}'>🖼 Фото</a>"
        if youtube:
            text += f" | <a href='{youtube}'>🎬 Видео</a>"

        markup = types.InlineKeyboardMarkup()
        view_btn = types.InlineKeyboardButton("👀 Показать полностью", callback_data=f"view_{recipe_id}")
        delete_btn = types.InlineKeyboardButton("🗑 Удалить", callback_data=f"del_{recipe_id}")
        markup.add(view_btn, delete_btn)

        bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('view_'))
def handle_view_favorite(call):
    """Показывает полный рецепт из избранного."""
    recipe_id = call.data.split('_')[1]
    user_id = call.from_user.id

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT recipe_name, recipe_thumb, recipe_instructions, recipe_youtube, ingredients, rating
        FROM favorites
        WHERE user_id = ? AND recipe_id = ?
    ''', (user_id, recipe_id))
    row = cursor.fetchone()
    conn.close()

    if not row:
        bot.answer_callback_query(call.id, "Рецепт не найден в избранном.")
        return

    name, thumb, instructions, youtube, ingredients, rating = row
    stars = '⭐' * rating + ('☆' * (5 - rating)) if rating else 'Без оценки'

    caption = f"<b>{name}</b>\nРейтинг: {stars}\n\n"
    caption += f"<b>📝 Ингредиенты:</b>\n{ingredients}\n\n"
    caption += f"<b>📖 Инструкция:</b>\n{instructions}\n"
    if youtube:
        caption += f"\n🎬 <a href='{youtube}'>Видеорецепт</a>"

    try:
        bot.send_photo(call.message.chat.id, thumb, caption=caption, parse_mode='HTML')
    except:
        bot.send_message(call.message.chat.id, caption, parse_mode='HTML')
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('del_'))
def handle_delete_favorite(call):
    """Удаляет рецепт из избранного."""
    recipe_id = call.data.split('_')[1]
    user_id = call.from_user.id
    delete_favorite(user_id, recipe_id)
    bot.edit_message_text(
        "🗑 Рецепт удалён из избранного.",
        call.message.chat.id,
        call.message.message_id
    )
    bot.answer_callback_query(call.id, "Удалено!")

# --- Запуск бота ---
if __name__ == "__main__":
    init_db()
    logger.info("Бот запущен")
    bot.polling(none_stop=True)