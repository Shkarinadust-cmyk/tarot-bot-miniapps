import os
import logging
import random
import sqlite3
import json
import hmac
import hashlib
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from flask import Flask, request, jsonify
from threading import Thread
from dotenv import load_dotenv
from openai import OpenAI

# Загружаем секреты
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Инициализация клиентов
client = OpenAI(api_key=OPENAI_API_KEY)
flask_app = Flask(__name__)

# База данных
def init_db():
    conn = sqlite3.connect('users.db')
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

def get_user_balance(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 10

def update_user_balance(user_id, new_balance):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, balance) 
        VALUES (?, ?)
    ''', (user_id, new_balance))
    conn.commit()
    conn.close()

def add_user_balance(user_id, additional_balance):
    current_balance = get_user_balance(user_id)
    new_balance = current_balance + additional_balance
    update_user_balance(user_id, new_balance)
    return new_balance

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

# GPT промпт для Таро
def create_tarot_prompt(user_question, cards):
    return f'''
Ты — мудрый таролог Спу́тник. Ты в совершенстве знаешь значения всех 78 карт Таро.
Пользователь спрашивает: "{user_question}"

Выпавшие карты: {", ".join(cards)}

**Структура ответа:**
1. **Обсуждение запроса** - кратко перефразируй вопрос
2. **Расклад** - назови расклад (например "Расклад на ситуацию")
3. **Интерпретация карт** - опиши каждую карту и их связь
4. **Итоговый совет** - ключевые выводы и рекомендации

**Требования:**
- Тон: спокойный, мудрый, поддерживающий
- Не более 10 предложений
- Используй эмодзи и **жирный шрифт**
- Напоминай о свободной воле человека
- Ответ должен быть на русском языке

Начни ответ с "✨" и закончи вопросом "Требуется ли еще что-то прояснить?"
'''

# Обработчики команд бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    balance = get_user_balance(user_id)
    
    # Обработка реферальных ссылок
    if context.args:
        args = context.args[0]
        if args.startswith('ref_'):
            referrer_id = int(args[4:])
            if referrer_id != user_id:
                # Добавляем бонусы обоим пользователям
                add_user_balance(referrer_id, 10)
                add_user_balance(user_id, 10)
                
                # Сохраняем в базу рефералов
                conn = sqlite3.connect('users.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO referrals (referrer_id, referred_id)
                    VALUES (?, ?)
                ''', (referrer_id, user_id))
                conn.commit()
                conn.close()
                
                await update.message.reply_text(
                    '🎉 **Вы получили 10 бесплатных вопросов за регистрацию по ссылке друга!**\n\n'
                    'Ваш друг тоже получил +10 вопросов. Приятного использования! ✨',
                    parse_mode='Markdown'
                )
    
    welcome_text = f'''
🔮 **Приветствую! Меня зовут Спу́тник.** 

Я мудрый советчик в мире Таро, готов помочь тебе прояснить ситуацию и найти ответы на твои вопросы.

**Что я умею:**
• Делать расклады на любые вопросы
• Толковать карты в контексте твоей ситуации  
• Поддерживать и направлять тебя

Просто напиши свой вопрос, и я проведу расклад! ✨

**Баланс вопросов:** {balance}
'''

    keyboard = [
        [InlineKeyboardButton("💎 Купить вопросы", web_app={'url': 'https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/'})],
        [InlineKeyboardButton("👥 Пригласить друзей", callback_data='invite')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    balance = get_user_balance(user_id)
    
    # Игнорируем простые приветствия
    simple_phrases = ['привет', 'hello', 'hi', 'start', 'начать', 'здравствуй', 'ку']
    if user_message.lower().strip() in simple_phrases:
        await update.message.reply_text(
            '✨ **Привет! Я Спу́тник - твой проводник в мире Таро.**\n\n'
            'Задай мне вопрос о ситуации, которая тебя волнует, и я проведу расклад карт! 🔮',
            parse_mode='Markdown'
        )
        return
    
    # Проверяем баланс для вопросов про карты
    tarot_keywords = ['карта', 'расклад', 'гадание', 'таро', 'будущее', 'завтра', 'предсказание', 'судьба', 'что будет', 'стоит ли']
    if any(keyword in user_message.lower() for keyword in tarot_keywords):
        if balance <= 0:
            await update.message.reply_text('''
❌ **Баланс закончился!**

Пополните баланс вопросов чтобы продолжить общение с картами:
https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/

Или пригласите друзей и получите +10 вопросов каждый! 👥
''')
            return
        
        # Уменьшаем баланс
        new_balance = balance - 1
        update_user_balance(user_id, new_balance)
        
        # Показываем "загрузку"
        thinking_msg = await update.message.reply_text(
            '🔄 *Загружаю карты...*\n'
            '_Соединяюсь с энергиями Вселенной..._ ✨',
            parse_mode='Markdown'
        )
        
        # Генерируем расклад (1-3 карты в зависимости от сложности вопроса)
        num_cards = 3 if len(user_message) > 20 else 1
        cards = [get_random_card() for _ in range(num_cards)]
        
        try:
            # Получаем ответ от GPT
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": create_tarot_prompt(user_message, cards)}],
                max_tokens=500,
                temperature=0.7
            )
            
            tarot_reading = response.choices[0].message.content
            
            # Удаляем сообщение "загрузки"
            await thinking_msg.delete()
            
            # Отправляем ответ
            final_message = f"{tarot_reading}\n\n🔮 **Осталось вопросов:** {new_balance}"
            await update.message.reply_text(final_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"GPT Error: {e}")
            await thinking_msg.delete()
            # Возвращаем списанный вопрос при ошибке
            update_user_balance(user_id, balance)
            await update.message.reply_text(
                '⚠️ **Произошла ошибка при подключении к мудрости Таро.**\n\n'
                'Попробуйте задать вопрос еще раз. Ваш вопрос не был списан.',
                parse_mode='Markdown'
            )
    
    else:
        # Обычные сообщения не тратят баланс
        responses = [
            "✨ Я здесь чтобы помочь тебе с раскладами Таро! Задай вопрос о ситуации которая тебя волнует.",
            "🔮 Я чувствую твое любопытство! Спроси меня о чем-то конкретном для точного расклада.",
            "💫 Готов исследовать твой вопрос через мудрость карт Таро. Что хочешь прояснить?",
            "🌙 Для работы с картами Таро задай вопрос о том, что тебя беспокоит или интересует."
        ]
        await update.message.reply_text(random.choice(responses))

async def invite_friends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    referral_link = f"https://t.me/SputnikTarobot?start=ref_{user_id}"
    
    text = f'''
👥 **Пригласи друзей и получи подарки!** 🎁

За каждую регистрацию по твоей ссылке:
• Ты получишь **+10 вопросов** 
• Друг получит **+10 вопросов**

**Твоя ссылка:**
`{referral_link}`

Просто отправь эту ссылку друзьям! 💫

*После регистрации друзей баланс обновится автоматически*
'''
    await query.message.reply_text(text, parse_mode='Markdown')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_user_balance(user_id)
    
    text = f'''
💎 **Твой баланс:** {balance} вопросов

https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/
'''
    keyboard = [
        [InlineKeyboardButton("💎 Купить вопросы", web_app={'url': 'https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/'})],
        [InlineKeyboardButton("👥 Пригласить друзей", callback_data='invite')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ВЕБХУКИ ЮКАССЫ
@flask_app.route('/webhook/yookassa', methods=['POST'])
def yookassa_webhook():
    try:
        # Получаем данные от ЮКассы
        event_json = request.get_json()
        logger.info(f"Yookassa webhook received: {event_json}")
        
        # Проверяем подпись (опционально, но рекомендуется)
        if not verify_yookassa_signature(request):
            logger.warning("Invalid Yookassa signature")
            return jsonify({'status': 'error', 'message': 'Invalid signature'}), 400
        
        # Обрабатываем событие
        event_type = event_json.get('event')
        object_data = event_json.get('object', {})
        
        if event_type == 'payment.succeeded':
            # Обработка успешного платежа
            payment_id = object_data.get('id')
            amount = object_data.get('amount', {}).get('value', 0)
            metadata = object_data.get('metadata', {})
            user_id = metadata.get('user_id')
            
            if user_id and amount > 0:
                # Определяем количество вопросов по сумме
                questions_map = {
                    300: 100,
                    600: 200, 
                    900: 300,
                    1500: 500,
                    3000: 1000
                }
                questions = questions_map.get(amount, amount // 3)  # По умолчанию 3 рубля за вопрос
                
                # Обновляем баланс пользователя
                new_balance = add_user_balance(int(user_id), questions)
                
                # Сохраняем информацию о платеже
                conn = sqlite3.connect('users.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO payments (payment_id, user_id, amount, status)
                    VALUES (?, ?, ?, ?)
                ''', (payment_id, user_id, questions, 'succeeded'))
                conn.commit()
                conn.close()
                
                logger.info(f"Payment succeeded: user {user_id} +{questions} questions, new balance: {new_balance}")
                
                # Отправляем уведомление пользователю
                try:
                    application = context.application
                    await application.bot.send_message(
                        chat_id=user_id,
                        text=f'🎉 **Оплата прошла успешно!**\n\n+{questions} вопросов добавлено на ваш баланс!\n\n💎 **Теперь у вас:** {new_balance} вопросов',
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification to user {user_id}: {e}")
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def verify_yookassa_signature(request):
    """Проверка подписи вебхука ЮКассы"""
    signature = request.headers.get('Authorization', '').replace('Bearer ', '')
    body = request.get_data(as_text=True)
    
    # Создаем HMAC подпись
    expected_signature = hmac.new(
        YOOKASSA_SECRET_KEY.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

# Запуск Flask сервера для вебхуков
def run_flask():
    flask_app.run(host='0.0.0.0', port=5000, debug=False)

# Основная функция
def main():
    # Инициализация базы данных
    init_db()
    
    # Запуск Flask в отдельном потоке
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Создание приложения Telegram бота
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CallbackQueryHandler(invite_friends, pattern='^invite$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    logger.info("Bot started successfully!")
    application.run_polling()

if __name__ == '__main__':
    main()