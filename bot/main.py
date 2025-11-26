import os
import logging
import random
import sqlite3
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from flask import Flask
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
    logger.error("❌ BOT_TOKEN не найден!")
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
                balance INTEGER DEFAULT 3
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
        return result[0] if result else 3
    except Exception as e:
        logger.error(f"❌ Ошибка баланса: {e}")
        return 3

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

def get_tarot_reading(user_question, cards):
    """Толкование через DeepSeek"""
    
    if not DEEPSEEK_API_KEY:
        logger.error("❌ DEEPSEEK_API_KEY не найден!")
        return get_fallback_reading(user_question, cards)
    
    prompt = f'''
Ты - таролог. Дай толкование расклада.

Вопрос: "{user_question}"
Карты: {", ".join(cards)}

Дай толкование на русском (5-7 предложений). Используй эмодзи.
'''
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        logger.info("🔄 Запрос к DeepSeek...")
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=10)
        
        logger.info(f"📡 Статус: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ Ошибка API: {response.status_code}")
            return get_fallback_reading(user_question, cards)
        
        result = response.json()
        reading = result['choices'][0]['message']['content']
        logger.info("✅ DeepSeek ответил!")
        
        return reading
        
    except Exception as e:
        logger.error(f"❌ Ошибка DeepSeek: {e}")
        return get_fallback_reading(user_question, cards)

def get_fallback_reading(user_question, cards):
    """Резервное толкование"""
    return f"""
✨ **Расклад на вопрос:** "{user_question}"

**Выпавшие карты:**
{', '.join(cards)}

**Толкование:**
Карты указывают на важный период в твоей жизни! Сейчас время доверять интуиции.

**Совет:**
Прислушайся к внутреннему голосу! 💫

Требуется ли еще что-то прояснить?
"""

# Обработчики команд бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        balance = get_user_balance(user_id)
        
        welcome_text = f'''
🔮 **Привет! Я Спу́тник - твой проводник в мире Таро.**

**Баланс:** {balance} раскладов

Задай вопрос о ситуации, и я сделаю расклад! ✨
'''

        keyboard = [
            [InlineKeyboardButton("💎 Купить расклады", web_app=WebAppInfo(url="https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/"))],
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
        simple_phrases = ['привет', 'hello', 'hi', 'start', 'начать', 'здравствуй', 'ку', 'хай', 'как дела', 'как ты']
        if user_message in simple_phrases:
            await update.message.reply_text('✨ Привет! Задай вопрос для расклада Таро.')
            return
        
        # КЛЮЧЕВЫЕ СЛОВА ДЛЯ РАСКЛАДА
        tarot_keywords = [
            '?', 'что', 'как', 'почему', 'когда', 'стоит ли', 'посоветуй',
            'помоги', 'подскажи', 'что делать', 'как быть', 'мне нужно',
            'хочу понять', 'не знаю', 'сомневаюсь', 'боюсь', 'волнуюсь',
            'работа', 'любов', 'деньг', 'отношен', 'будущ', 'завтра',
            'ситуац', 'проблем', 'вопрос', 'совет', 'рекомендац',
            'карт', 'таро', 'расклад', 'гадан', 'погадай', 'предскаж'
        ]
        
        # Проверяем есть ли ключевые слова И сообщение не слишком короткое
        has_keywords = any(keyword in user_message for keyword in tarot_keywords)
        is_long_enough = len(user_message) > 5
        
        logger.info(f"🔍 Ключевые слова: {has_keywords}, Длина: {is_long_enough}")
        
        if has_keywords and is_long_enough:
            # ЭТО ВОПРОС ДЛЯ РАСКЛАДА
            if balance <= 0:
                await update.message.reply_text(
                    '❌ **Баланс закончился!**\n\n'
                    'Пополни в мини-приложении:\n'
                    'https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/',
                    parse_mode='Markdown'
                )
                return
            
            # СПИСЫВАЕМ БАЛАНС И ДЕЛАЕМ РАСКЛАД
            new_balance = balance - 1
            update_user_balance(user_id, new_balance)
            
            thinking_msg = await update.message.reply_text('🔄 **Вытягиваю карты...**', parse_mode='Markdown')
            
            await asyncio.sleep(2)
            
            # ДЕЛАЕМ РАСКЛАД
            cards = [get_random_card() for _ in range(3)]
            reading = get_tarot_reading(update.message.text, cards)
            
            await thinking_msg.delete()
            
            # ОТПРАВЛЯЕМ РАСКЛАД
            final_message = f"{reading}\n\n🔮 **Осталось раскладов:** {new_balance}"
            await update.message.reply_text(final_message, parse_mode='Markdown')
            
        else:
            # ОБЫЧНЫЕ СООБЩЕНИЯ
            await update.message.reply_text('🔮 Задай вопрос о ситуации для расклада Таро!')
            
    except Exception as e:
        logger.error(f"❌ Ошибка handle_message: {e}")
        await update.message.reply_text('⚠️ Ошибка. Попробуй еще раз.')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    balance = get_user_balance(user_id)
    await update.message.reply_text(f'💎 Баланс: {balance} раскладов')

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