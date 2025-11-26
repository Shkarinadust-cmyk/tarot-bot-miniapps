import os
import logging
import random
import sqlite3
import asyncio
import requests
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from flask import Flask, jsonify
from threading import Thread
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загружаем секреты
load_dotenv()

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден! Проверь Secrets в Replit.")
    exit(1)

logger.info(f"✅ BOT_TOKEN загружен: {BOT_TOKEN[:10]}...")
if DEEPSEEK_API_KEY:
    logger.info(f"✅ DEEPSEEK_API_KEY загружен: {DEEPSEEK_API_KEY[:10]}...")
else:
    logger.warning("❌ DEEPSEEK_API_KEY не найден! Будет использоваться резервный режим.")

# Инициализация Flask
flask_app = Flask(__name__)

# База данных
def init_db():
    try:
        conn = sqlite3.connect('users.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 10,
                referral_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                user_id INTEGER,
                amount INTEGER,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                referrer_id INTEGER,
                referred_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (referrer_id, referred_id)
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")

def get_user_balance(user_id):
    try:
        conn = sqlite3.connect('users.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 10
    except Exception as e:
        logger.error(f"❌ Ошибка получения баланса: {e}")
        return 10

def update_user_balance(user_id, new_balance):
    try:
        conn = sqlite3.connect('users.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, balance) 
            VALUES (?, ?)
        ''', (user_id, new_balance))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка обновления баланса: {e}")
        return False

def add_user_balance(user_id, additional_balance):
    try:
        current_balance = get_user_balance(user_id)
        new_balance = current_balance + additional_balance
        if update_user_balance(user_id, new_balance):
            return new_balance
        return current_balance
    except Exception as e:
        logger.error(f"❌ Ошибка добавления баланса: {e}")
        return get_user_balance(user_id)

# Карты Таро
tarot_cards = {
    "major": [
        "🃏 Шут", "🧙‍♂️ Маг", "🔮 Верховная Жрица", "👑 Императрица", 
        "🏛 Император", "🕌 Иерофант", "💑 Влюбленные", "🐎 Колесница",
        "⚖️ Справедливость", "🧘‍♂️ Отшельник", "🎡 Колесо Фортуны",
        "💪 Сила", "♒️ Повешенный", "💀 Смерть", "🕊 Умеренность",
        "😈 Дьявол", "⚡️ Башня", "⭐️ Звезда", "🌙 Луна", "☀️ Солнце",
        "👨‍⚖️ Суд", "🌍 Мир"
    ],
    "minor": [
        "Туз Жезлов", "Двойка Жезлов", "Тройка Жезлов", "Четверка Жезлов",
        "Пятерка Жезлов", "Шестерка Жезлов", "Семерка Жезлов", "Восьмерка Жезлов",
        "Девятка Жезлов", "Десятка Жезлов", "Паж Жезлов", "Рыцарь Жезлов",
        "Королева Жезлов", "Король Жезлов",
        "Туз Кубков", "Двойка Кубков", "Тройка Кубков", "Четверка Кубков",
        "Пятерка Кубков", "Шестерка Кубков", "Семерка Кубков", "Восьмерка Кубков",
        "Девятка Кубков", "Десятка Кубков", "Паж Кубков", "Рыцарь Кубков",
        "Королева Кубков", "Король Кубков",
        "Туз Мечей", "Двойка Мечей", "Тройка Мечей", "Четверка Мечей",
        "Пятерка Мечей", "Шестерка Мечей", "Семерка Мечей", "Восьмерка Мечей",
        "Девятка Мечей", "Десятка Мечей", "Паж Мечей", "Рыцарь Мечей",
        "Королева Мечей", "Король Мечей",
        "Туз Пентаклей", "Двойка Пентаклей", "Тройка Пентаклей", "Четверка Пентаклей",
        "Пятерка Пентаклей", "Шестерка Пентаклей", "Семерка Пентаклей", "Восьмерка Пентаклей",
        "Девятка Пентаклей", "Десятка Пентаклей", "Паж Пентаклей", "Рыцарь Пентаклей",
        "Королева Пентаклей", "Король Пентаклей"
    ]
}

def get_random_card():
    card_type = random.choice(["major", "minor"])
    card = random.choice(tarot_cards[card_type])
    position = random.choice(["прямое", "перевернутое"])
    return f"{card} ({position})"

def get_tarot_reading(user_question, cards):
    """Получаем толкование от DeepSeek"""
    
    if not DEEPSEEK_API_KEY:
        logger.warning("⚠️ DeepSeek API ключ не найден, используем резервный режим")
        return get_fallback_reading(user_question, cards)
    
    prompt = f'''
Ты - мудрый таролог Спу́тник. Ты в совершенстве знаешь значения всех 78 карт Таро.

Вопрос пользователя: "{user_question}"
Выпавшие карты: {", ".join(cards)}

Дай точное и поддерживающее толкование расклада:
1. Кратко обсуди запрос
2. Объяви название расклада 
3. Проинтерпретируй каждую карту в контексте вопроса
4. Свяжи значения карт между собой
5. Дай итоговый совет

Требования:
- Тон: спокойный, мудрый, поддерживающий
- Не более 8-10 предложений
- Используй эмодзи и **жирный шрифт**
- Напомни о свободной воле
- Начни с "✨" и закончи вопросом "Требуется ли еще что-то прояснить?"
- Ответ на русском языке
'''
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system", 
                    "content": "Ты мудрый таролог Спу́тник. Ты даешь точные, поддерживающие толкования карт Таро. Ты спокоен, мудр, внимателен к деталям. Ты используешь эмодзи и жирный шрифт. Твои ответы не более 10 предложений на русском языке."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 800,
            "temperature": 0.7
        }
        
        logger.info("🔄 Отправляем запрос к DeepSeek API...")
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        reading = result['choices'][0]['message']['content']
        logger.info("✅ Получен ответ от DeepSeek")
        
        return reading
        
    except Exception as e:
        logger.error(f"❌ Ошибка DeepSeek: {e}")
        return get_fallback_reading(user_question, cards)

def get_fallback_reading(user_question, cards):
    """Резервное толкование если API не работает"""
    return f"""
✨ **Расклад на вопрос:** "{user_question}"

**Выпавшие карты:**
{', '.join(cards)}

**Толкование:**
Карты указывают на **период изменений** и новых возможностей в твоей жизни! Каждая карта рассказывает свою часть истории, вместе создавая целостную картину твоего пути.

**Совет:**
**Слушай свою интуицию** и будь открыт к знакам судьбы. Помни - у тебя есть сила влиять на свое будущее! 💫

Требуется ли еще что-то прояснить?
"""

# Обработчики команд бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
        user_id = update.message.from_user.id
        balance = get_user_balance(user_id)
        
        # Обработка реферальных ссылок
        if context.args:
            args = context.args[0]
            if args.startswith('ref_'):
                referrer_id = int(args[4:])
                if referrer_id != user_id:
                    add_user_balance(referrer_id, 10)
                    add_user_balance(user_id, 10)
                    await update.message.reply_text(
                        '🎉 **+10 вопросов за регистрацию друга!**\n\n'
                        'Твой друг тоже получил +10 вопросов. Приятного использования! ✨',
                        parse_mode='Markdown'
                    )
        
        welcome_text = f'''
🔮 **Приветствую! Меня зовут Спу́тник.** 

Я мудрый советчик в мире Таро, готов помочь тебе прояснить ситуацию и найти ответы на волнующие вопросы.

**Баланс вопросов:** {balance}

Просто напиши свой вопрос, и я проведу расклад! ✨
'''

        web_app_url = "https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/"
        keyboard = [
            [InlineKeyboardButton("💎 Купить вопросы", web_app=WebAppInfo(url=web_app_url))],
            [InlineKeyboardButton("👥 Пригласить друзей", callback_data='invite')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ Ошибка в start: {e}")
        if update.message:
            await update.message.reply_text('🔮 Привет! Напиши мне свой вопрос для расклада Таро! ✨')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return
            
        user_id = update.message.from_user.id
        user_message = update.message.text
        balance = get_user_balance(user_id)
        
        # Игнорируем простые приветствия
        simple_phrases = ['привет', 'hello', 'hi', 'start', 'начать', 'здравствуй', 'ку', 'хай']
        if user_message.lower().strip() in simple_phrases:
            await update.message.reply_text(
                '✨ **Привет! Я Спу́тник** - твой мудрый советчик в мире Таро.\n\n'
                'Задай вопрос о ситуации, которая тебя волнует, и я проведу точный расклад карт! 🔮',
                parse_mode='Markdown'
            )
            return
        
        # Проверяем баланс для вопросов про карты
        tarot_keywords = [
            'карта', 'расклад', 'гадание', 'таро', 'будущее', 'завтра', 
            'предсказание', 'судьба', 'что будет', 'стоит ли', 'посоветуй',
            'любовь', 'работа', 'деньги', 'отношения', 'здоровье', 'семья',
            'ситуация', 'будущ', 'жизн', 'как быть'
        ]
        
        is_tarot_question = any(keyword in user_message.lower() for keyword in tarot_keywords)
        
        if is_tarot_question:
            if balance <= 0:
                await update.message.reply_text(
                    '❌ **Баланс вопросов закончился!**\n\n'
                    'Пополни баланс чтобы продолжить:\n'
                    'https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/',
                    parse_mode='Markdown'
                )
                return
            
            # Уменьшаем баланс
            new_balance = balance - 1
            update_user_balance(user_id, new_balance)
            
            # Показываем "загрузку"
            thinking_msg = await update.message.reply_text(
                '🔄 **Загружаю карты...**\n'
                '_Соединяюсь с энергиями Вселенной..._ ✨',
                parse_mode='Markdown'
            )
            
            # Ждем немного для реализма
            await asyncio.sleep(2)
            
            # Генерируем расклад
            num_cards = 3 if len(user_message) > 15 else random.randint(1, 2)
            cards = [get_random_card() for _ in range(num_cards)]
            
            # Получаем толкование
            tarot_reading = get_tarot_reading(user_message, cards)
            
            # Удаляем сообщение "загрузки"
            await thinking_msg.delete()
            
            # Отправляем ответ
            final_message = f"{tarot_reading}\n\n🔮 **Осталось вопросов:** {new_balance}"
            await update.message.reply_text(final_message, parse_mode='Markdown')
            
        else:
            # Обычные сообщения не тратят баланс
            responses = [
                "✨ Я здесь чтобы помочь тебе с раскладами Таро! Задай вопрос о ситуации которая тебя волнует.",
                "🔮 Что хочешь прояснить с помощью карт Таро?",
                "💫 Готов к раскладу! О чем твой вопрос?",
                "🌙 Задай вопрос о том, что тебя беспокоит, и я помогу с раскладом карт!"
            ]
            await update.message.reply_text(random.choice(responses))
            
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_message: {e}")
        if update.message:
            await update.message.reply_text('⚠️ Произошла ошибка. Попробуй еще раз.')

async def invite_friends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.callback_query or not update.callback_query.message:
            return
            
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        referral_link = f"https://t.me/SputnikTarobot?start=ref_{user_id}"
        
        text = f'''
👥 **Пригласи друзей!** 🎁

За регистрацию по твоей ссылке:
• Ты получишь **+10 вопросов** 
• Друг получит **+10 вопросов**

**Твоя ссылка:**
`{referral_link}`
'''
        await query.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ Ошибка в invite_friends: {e}")

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
        user_id = update.message.from_user.id
        balance = get_user_balance(user_id)
        
        text = f'💎 **Твой баланс:** {balance} вопросов'
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ Ошибка в balance: {e}")

# Вебхуки ЮКассы
@flask_app.route('/webhook/yookassa', methods=['POST'])
def yookassa_webhook():
    try:
        logger.info("🔄 Получен вебхук от ЮКассы")
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка вебхука: {e}")
        return jsonify({'status': 'error'}), 500

@flask_app.route('/')
def home():
    return '🟢 Таро бот работает!'

# Запуск Flask сервера
def run_flask():
    flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

# Основная функция
def main():
    logger.info("🟢 Запуск Таро бота с DeepSeek...")
    
    # Инициализация базы данных
    init_db()
    
    # Запуск Flask в отдельном потоке
    try:
        flask_thread = Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        logger.info("🟢 Flask сервер запущен на порту 5000")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска Flask: {e}")
    
    # Создание приложения Telegram бота
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("balance", balance_command))
        application.add_handler(CallbackQueryHandler(invite_friends, pattern='^invite$'))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Запуск бота
        logger.info("✅ Бот успешно запущен!")
        logger.info("🔮 Бот: @SputnikTarobot")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка бота: {e}")

if __name__ == '__main__':
    main()