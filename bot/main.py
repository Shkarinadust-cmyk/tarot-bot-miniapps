import os
import logging
import random
import sqlite3
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
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

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден!")
    exit(1)

logger.info("✅ Бот запускается...")

# База данных
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 3
        )
    ''')
    conn.commit()
    conn.close()

def get_user_balance(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 3

def update_user_balance(user_id, new_balance):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, balance) 
        VALUES (?, ?)
    ''', (user_id, new_balance))
    conn.commit()
    conn.close()

# Карты Таро
tarot_cards = [
    "🃏 Шут", "🧙‍♂️ Маг", "🔮 Верховная Жрица", "👑 Императрица", 
    "🏛 Император", "🕌 Иерофант", "💑 Влюбленные", "🐎 Колесница",
    "⚖️ Справедливость", "🧘‍♂️ Отшельник", "🎡 Колесо Фортуны",
    "💪 Сила", "♒️ Повешенный", "💀 Смерть", "🕊 Умеренность"
]

def get_random_card():
    card = random.choice(tarot_cards)
    position = random.choice(["прямое", "перевернутое"])
    return f"{card} ({position})"

def get_tarot_reading(user_question, cards):
    """Толкование через DeepSeek"""
    
    if not DEEPSEEK_API_KEY:
        return "❌ API ключ не настроен"
    
    prompt = f'''
Ты - таролог. Дай толкование расклада на русском языке.

Вопрос: "{user_question}"
Карты: {", ".join(cards)}

Дай толкование (5-7 предложений). Используй эмодзи.
Тон: поддерживающий, мудрый.
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
        
        response = requests.post("https://api.deepseek.com/v1/chat/completions", 
                               headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"❌ Ошибка API: {response.status_code}"
            
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

# Обработчики команд бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_user_balance(user_id)
    
    welcome_text = f'''
🔮 **Привет! Я бот Таро.**

У тебя {balance} раскладов.

Напиши вопрос для расклада карт!
'''

    keyboard = [
        [InlineKeyboardButton("💎 Купить расклады", web_app=WebAppInfo(url="https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/"))],
        [InlineKeyboardButton("👥 Пригласить друзей", callback_data='invite')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    balance = get_user_balance(user_id)
    
    print(f"Получено сообщение: {user_message}")
    
    # Простые фразы - не списываем баланс
    if user_message.lower() in ['привет', 'hello', 'hi', 'start', 'начать']:
        await update.message.reply_text('Привет! Напиши вопрос для расклада Таро.')
        return
    
    # ВСЕ остальные сообщения считаем вопросами для расклада
    if balance <= 0:
        await update.message.reply_text('❌ Баланс закончился! Пополни в мини-приложении.')
        return
    
    # Списываем баланс
    new_balance = balance - 1
    update_user_balance(user_id, new_balance)
    
    # Делаем расклад
    cards = [get_random_card() for _ in range(3)]
    
    # Получаем толкование от DeepSeek
    reading = get_tarot_reading(user_message, cards)
    
    final_message = f"""
✨ **Расклад на вопрос:** "{user_message}"

**Выпавшие карты:**
{', '.join(cards)}

**Толкование:**
{reading}

🔮 **Осталось раскладов:** {new_balance}
"""
    
    await update.message.reply_text(final_message, parse_mode='Markdown')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_user_balance(user_id)
    await update.message.reply_text(f'💎 Баланс: {balance} раскладов')

async def invite_friends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    link = f"https://t.me/SputnikTarobot?start=ref_{user_id}"
    await query.message.reply_text(f'Пригласи друга: {link}')

def main():
    logger.info("🔄 Инициализация базы данных...")
    init_db()
    
    logger.info("🚀 Создание приложения бота...")
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CallbackQueryHandler(invite_friends, pattern='^invite$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Бот запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()