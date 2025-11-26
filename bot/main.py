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

# Проверка ключей
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
        "Королева Кубков", "Король Кубков"
    ]
}

def get_random_card():
    card_type = random.choice(["major", "minor"])
    card = random.choice(tarot_cards[card_type])
    position = random.choice(["прямое", "перевернутое"])
    return f"{card} ({position})"

def get_tarot_reading(user_question, cards):
    """Толкование через DeepSeek"""
    
    if not DEEPSEEK_API_KEY:
        logger.error("❌ DEEPSEEK_API_KEY не найден!")
        return get_fallback_reading(user_question, cards)
    
    prompt = f'''
Ты - мудрый, эмпатичный таролог Спу́тник. Ты разговариваешь с клиентом тепло и поддерживающе.

Вопрос клиента: "{user_question}"
Выпавшие карты: {", ".join(cards)}

Дай развернутое, глубокое толкование (8-12 предложений):
1. Начни с эмпатичного понимания ситуации
2. Подробно проанализируй каждую карту в контексте вопроса
3. Покажи связи между картами
4. Дай практические советы и поддержку
5. Закончи ободряющими словами

Тон: теплый, мудрый, поддерживающий, человечный.
Используй эмодзи и жирный шрифт для акцентов.
'''
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800,
            "temperature": 0.7
        }
        
        logger.info("🔄 Отправляю запрос к DeepSeek API...")
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=15)
        
        logger.info(f"📡 Статус ответа: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ Ошибка API: {response.status_code}")
            return get_fallback_reading(user_question, cards)
        
        result = response.json()
        reading = result['choices'][0]['message']['content']
        logger.info("🎯 DeepSeek сработал!")
        
        return reading
        
    except Exception as e:
        logger.error(f"❌ Ошибка DeepSeek: {e}")
        return get_fallback_reading(user_question, cards)

def get_fallback_reading(user_question, cards):
    """Резервное толкование"""
    return f"""
✨ **Дорогой друг, я чувствую твой вопрос всей душой...** 

Ты спрашиваешь: *"{user_question}"*

**Карты, которые выпали:**
{', '.join(cards)}

**Мое понимание твоей ситуации:**
Каждая из этих карт рассказывает важную часть твоей истории. Вместе они создают удивительную картину твоего пути - полного смысла и возможностей для роста.

**Глубокое толкование:**
Эти карты говорят о периоде трансформации, когда важно слушать свое сердце. Я вижу, как каждая карта поддерживает другую, создавая гармоничный поток энергии в твою жизнь.

**Практический совет:**
Позволь себе довериться текущему моменту. Иногда самые важные ответы приходят, когда мы перестаем искать их так усердно.

**Поддержка:**
Знай, что у тебя есть все необходимое для этого пути. Я здесь, чтобы поддержать тебя в моменты сомнений 💫

Хочешь глубже исследовать какую-то конкретную карту?
"""

# Обработчики команд бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
        user_id = update.message.from_user.id
        balance = get_user_balance(user_id)
        
        welcome_text = f'''
💫 **Привет, дорогой друг! Я Спу́тник.** 

Я твой мудрый проводник в мире Таро, готовый поддержать тебя и помочь найти ответы в сердце.

**У тебя есть {balance} расклада** для глубокого погружения в твои вопросы.

Расскажи, что тебя волнует, и я аккуратно помогу прояснить ситуацию через мудрость карт 🌙
'''

        keyboard = [
            [InlineKeyboardButton("💎 Пополнить расклады", web_app=WebAppInfo(url="https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/"))],
            [InlineKeyboardButton("👥 Пригласить друзей", callback_data='invite')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ Ошибка start: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message or not update.message.text:
            return
            
        user_id = update.message.from_user.id
        user_message = update.message.text.strip()
        balance = get_user_balance(user_id)
        
        logger.info(f"📨 Сообщение от {user_id}: {user_message}")
        
        # Игнорируем команды
        if user_message.startswith('/'):
            return
        
        # Инициализируем контекст пользователя
        if 'user_context' not in context.user_data:
            context.user_data['user_context'] = {}
        
        user_context = context.user_data['user_context']
        
        # Если ждем подтверждения расклада
        if user_context.get('waiting_confirmation'):
            user_message_lower = user_message.lower()
            
            # Положительные ответы
            if any(word in user_message_lower for word in ['да', 'yes', 'конечно', 'сделай', 'хочу', 'ага', 'пожалуйста', 'давай']):
                if balance <= 0:
                    await update.message.reply_text(
                        '💔 **У тебя закончились расклады, родной...**\n\n'
                        'Но это легко исправить! Пополни баланс в мини-приложении, '
                        'и я с радостью сделаю для тебя глубокий расклад ✨\n\n'
                        'https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/',
                        parse_mode='Markdown'
                    )
                    user_context['waiting_confirmation'] = False
                    return
                
                # Подтвердили - делаем расклад
                original_question = user_context.get('pending_question', '')
                new_balance = balance - 1
                update_user_balance(user_id, new_balance)
                
                thinking_msg = await update.message.reply_text(
                    '🌙 **Вытягиваю карты...**\n'
                    '_Прислушиваюсь к их мудрости, чувствую твою энергию..._ ✨',
                    parse_mode='Markdown'
                )
                
                await asyncio.sleep(3)
                
                cards = [get_random_card() for _ in range(3)]
                reading = get_tarot_reading(original_question, cards)
                
                await thinking_msg.delete()
                
                final_message = f"{reading}\n\n💫 **Осталось раскладов:** {new_balance}"
                await update.message.reply_text(final_message, parse_mode='Markdown')
                
                # Сбрасываем состояние
                user_context['waiting_confirmation'] = False
                user_context['pending_question'] = None
                
            # Отрицательные ответы
            elif any(word in user_message_lower for word in ['нет', 'no', 'не надо', 'отмена', 'передумал']):
                await update.message.reply_text(
                    'Понимаю, родной 🤍\n\n'
                    'Иногда нужно время, чтобы настроиться на расклад.\n'
                    'Когда будешь готов - просто расскажи, что на душе. '
                    'Я всегда здесь для тебя 🌙'
                )
                user_context['waiting_confirmation'] = False
                user_context['pending_question'] = None
            else:
                await update.message.reply_text(
                    'Просто скажи "да" если хочешь расклад, или "нет" если сейчас не время 🤗\n'
                    'Я почувствую твое решение сердцем.'
                )
            return
        
        # Анализируем новое сообщение
        message_lower = user_message.lower()
        
        # Приветствия и простые фразы
        simple_phrases = ['привет', 'hello', 'hi', 'хай', 'ку', 'здравствуй', 'салют', 'прив']
        if message_lower in simple_phrases:
            await update.message.reply_text(
                '💫 Привет, родной! Как твое сердце сегодня?\n\n'
                'Расскажи, что тебя волнует - вместе посмотрим, '
                'какую мудрость приготовили для нас карты 🌙'
            )
            return
        
        # Фразы про бота и таро
        bot_phrases = ['спутник', 'бот', 'таро', 'карты', 'кто ты', 'что ты']
        if any(phrase in message_lower for phrase in bot_phrases) and len(user_message) < 20:
            await update.message.reply_text(
                'Я Спу́тник - твой мудрый друг и проводник в мире Таро 🌙\n\n'
                'Я здесь не чтобы предсказывать будущее, а чтобы помочь тебе '
                'услышать мудрость собственного сердца через язык карт.\n\n'
                'Что лежит у тебя на душе, родной?'
            )
            return
        
        # Вопросы и темы для раскладов
        question_patterns = [
            'что', 'как', 'почему', 'когда', 'стоит ли', 'посоветуй',
            'помоги', 'подскажи', 'что делать', 'как быть', 'мне нужно',
            'хочу понять', 'не знаю', 'сомневаюсь', 'боюсь', 'волнуюсь'
        ]
        
        tarot_keywords = [
            'расклад', 'гадание', 'погадай', 'предскажи', 'карты таро',
            'хочу расклад', 'сделай расклад', 'посмотри на картах'
        ]
        
        is_question = any(pattern in message_lower for pattern in question_patterns)
        is_tarot_request = any(keyword in message_lower for keyword in tarot_keywords)
        
        # Если прямо просит расклад или это явный вопрос
        if is_tarot_request or (is_question and len(user_message) > 10):
            if balance <= 0:
                await update.message.reply_text(
                    '💔 **Родной, у тебя закончились расклады...**\n\n'
                    'Но я чувствую, как важно для тебя это обращение к картам!\n\n'
                    'Пополни баланс в мини-приложении, и я с глубоким вниманием '
                    'сделаю для тебя расклад:\n'
                    'https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/',
                    parse_mode='Markdown'
                )
                return
            
            # Предлагаем подтверждение расклада
            user_context['waiting_confirmation'] = True
            user_context['pending_question'] = user_message
            
            if is_tarot_request:
                confirmation_text = (
                    f'💫 **Я чувствую твое желание обратиться к картам...**\n\n'
                    f'Ты хочешь, чтобы я сделал расклад на твой запрос?\n\n'
                    f'Это займет 1 из твоих {balance} раскладов.\n\n'
                    f'**Скажешь "да" - и мы начнем это волшебное путешествие?** 🌙'
                )
            else:
                confirmation_text = (
                    f'💫 **Я слышу твой вопрос всем сердцем...**\n\n'
                    f'Ты спрашиваешь: *"{user_message}"*\n\n'
                    f'Я могу сделать глубокий расклад Таро, чтобы помочь тебе '
                    f'увидеть ситуацию с новой perspective.\n\n'
                    f'Это займет 1 из твоих {balance} раскладов.\n\n'
                    f'**Хочешь, чтобы я вытянул карты для тебя?** ✨'
                )
            
            await update.message.reply_text(confirmation_text, parse_mode='Markdown')
            
        else:
            # Общие разговоры - мягко возвращаем к Таро
            responses = [
                'Я чувствую твои слова... Знаешь, карты часто помогают '
                'увидеть то, что скрыто от обычного взгляда. Хочешь '
                'обратиться к их мудрости? 🌙',
                
                'Понимаю тебя... Иногда самые ясные ответы приходят '
                'через тихий диалог с картами. Расскажи, что именно '
                'тебя волнует - вместе посмотрим, что говорят звезды ✨',
                
                'Я здесь, чтобы поддержать тебя через мудрость Таро. '
                'Что лежит у тебя на сердце, родной? Давай посмотрим, '
                'какую мудрость приготовили для нас карты сегодня 💫'
            ]
            
            await update.message.reply_text(random.choice(responses))
            
    except Exception as e:
        logger.error(f"❌ Ошибка handle_message: {e}")
        await update.message.reply_text(
            '💔 Что-то пошло не так в моем сердце...\n'
            'Попробуй, пожалуйста, еще раз. Я здесь для тебя 🌙'
        )

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return
            
        user_id = update.message.from_user.id
        balance = get_user_balance(user_id)
        
        balance_text = (
            f'💫 **У тебя {balance} расклад{"ов" if balance != 1 else ""}**\n\n'
            f'Каждый расклад - это возможность глубоко погрузиться в твой вопрос '
            f'и найти ответы, которые уже ждут тебя в сердце 🌙\n\n'
            f'Когда будешь готов - просто поделись тем, что тебя волнует.'
        )
        
        await update.message.reply_text(balance_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ Ошибка balance: {e}")

async def invite_friends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.callback_query:
            return
            
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        link = f"https://t.me/SputnikTarobot?start=ref_{user_id}"
        
        invite_text = (
            f'👥 **Поделись мудростью с близкими!** 💫\n\n'
            f'Пригласи друзей - и вы оба получите по **+3 расклада**!\n\n'
            f'Просто отправь им эту ссылку:\n`{link}`\n\n'
            f'Вместе мы создадим пространство поддержки и мудрости 🌙'
        )
        
        await query.message.reply_text(invite_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ Ошибка invite: {e}")

@flask_app.route('/')
def home():
    return '💫 Таро бот Спу́тник работает с любовью!'

def run_flask():
    flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def main():
    logger.info("🚀 Запуск Спу́тника...")
    
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
    
    logger.info("✅ Спу́тник запущен! Готов поддерживать сердца...")
    application.run_polling()

if __name__ == '__main__':
    main()