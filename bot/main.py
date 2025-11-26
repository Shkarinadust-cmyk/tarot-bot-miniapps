import os
import logging
import random
import sqlite3
import asyncio
import requests
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

# ЖЕСТКАЯ ПРОВЕРКА КЛЮЧЕЙ
if not BOT_TOKEN:
    logger.error("❌ CRITICAL: BOT_TOKEN не найден!")
    exit(1)

logger.info(f"🔑 BOT_TOKEN: {BOT_TOKEN[:10]}...")
logger.info(f"🔑 DEEPSEEK_KEY: {DEEPSEEK_API_KEY[:10] if DEEPSEEK_API_KEY else 'NOT FOUND'}")

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
                balance INTEGER DEFAULT 10
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("✅ База данных готова")
    except Exception as e:
        logger.error(f"❌ Ошибка БД: {e}")

def get_user_balance(user_id):
    try:
        conn = sqlite3.connect('users.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 10
    except Exception as e:
        logger.error(f"❌ Ошибка баланса: {e}")
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
        logger.error(f"❌ Ошибка обновления: {e}")
        return False

# Карты Таро
tarot_cards = [
    "🃏 Шут", "🧙‍♂️ Маг", "🔮 Верховная Жрица", "👑 Императрица", 
    "🏛 Император", "🕌 Иерофант", "💑 Влюбленные", "🐎 Колесница",
    "⚖️ Справедливость", "🧘‍♂️ Отшельник", "🎡 Колесо Фортуны",
    "💪 Сила", "♒️ Повешенный", "💀 Смерть", "🕊 Умеренность",
    "😈 Дьявол", "⚡️ Башня", "⭐️ Звезда", "🌙 Луна", "☀️ Солнце",
    "👨‍⚖️ Суд", "🌍 Мир"
]

def get_random_card():
    card = random.choice(tarot_cards)
    position = random.choice(["прямое", "перевернутое"])
    return f"{card} ({position})"

BOT_TOKEN=8355095598:AAGi48QWU-4e66ZTR2qMYU6aiK-Py1TxjWU

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        balance = get_user_balance(user_id)
        
        welcome_text = f'''
🔮 **Привет! Я Спу́тник - твой проводник в мире Таро.**

**Баланс:** {balance} вопросов

Задай вопрос о ситуации, и я сделаю расклад! ✨
'''

        keyboard = [
            [InlineKeyboardButton("💎 Купить вопросы", web_app=WebAppInfo(url="https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/"))],
            [InlineKeyboardButton("👥 Пригласить друзей", callback_data='invite')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ Ошибка start: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        user_message = update.message.text.strip().lower()
        balance = get_user_balance(user_id)
        
        logger.info(f"📨 Сообщение от {user_id}: {user_message}")
        
        # ПРОСТЫЕ ФРАЗЫ - не списываем баланс
        simple_phrases = ['привет', 'hello', 'hi', 'start', 'начать', 'здравствуй', 'ку', 'хай']
        if user_message in simple_phrases:
            await update.message.reply_text('✨ Привет! Задай вопрос для расклада Таро.')
            return
        
        # ВОПРОСЫ ДЛЯ РАСКЛАДА - списываем баланс
        tarot_keywords = ['таро', 'карт', 'расклад', 'гадан', 'будущ', 'завтра', 'судьб', 'любов', 'работ', 'денег', 'отношен', 'что будет', 'стоит ли', 'посоветуй', 'что мне']
        
        is_tarot_question = any(keyword in user_message for keyword in tarot_keywords)
        logger.info(f"🔍 Это вопрос для расклада? {is_tarot_question}")
        
        if is_tarot_question:
            if balance <= 0:
                await update.message.reply_text('❌ Баланс пуст! Пополни в мини-приложении.')
                return
            
            # СПИСЫВАЕМ БАЛАНС
            new_balance = balance - 1
            update_user_balance(user_id, new_balance)
            
            thinking_msg = await update.message.reply_text('🔄 Вытягиваю карты...')
            
            # ДЕЛАЕМ РАСКЛАД
            cards = [get_random_card() for _ in range(3)]
            reading = get_tarot_reading(update.message.text, cards)
            
            await thinking_msg.delete()
            await update.message.reply_text(f"{reading}\n\n🔮 Осталось вопросов: {new_balance}", parse_mode='Markdown')
            
        else:
            # ОБЫЧНЫЕ СООБЩЕНИЯ
            await update.message.reply_text('🔮 Задай вопрос о ситуации для расклада Таро!')
            
    except Exception as e:
        logger.error(f"❌ Ошибка handle_message: {e}")
        await update.message.reply_text('⚠️ Ошибка. Попробуй еще раз.')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    balance = get_user_balance(user_id)
    await update.message.reply_text(f'💎 Баланс: {balance} вопросов')

async def invite_friends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    link = f"https://t.me/SputnikTarobot?start=ref_{user_id}"
    await query.message.reply_text(f'👥 Пригласи друга: `{link}`', parse_mode='Markdown')

@flask_app.route('/')
def home():
    return '✅ Бот работает!'

def run_flask():
    flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def main():
    logger.info("🚀 ЗАПУСК БОТА...")
    
    init_db()
    
    # Flask в отдельном потоке
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Запуск бота
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CallbackQueryHandler(invite_friends, pattern='^invite$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ БОТ ЗАПУЩЕН! Проверяй в Telegram...")
    application.run_polling()

if __name__ == '__main__':
    main()