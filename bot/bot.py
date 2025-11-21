import os
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import sqlite3
from datetime import datetime
import openai

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8355095598:AAGi48QWU-4e66ZTR2qMYU6aiK-Py1TxjWU"
OPENAI_API_KEY = "your_openai_api_key_here"  # Получите на platform.openai.com
ADMIN_CHAT_ID = "your_chat_id_here"  # Ваш ID в Telegram

# Инициализация OpenAI
openai.api_key = OPENAI_API_KEY

# Карты Таро (старшие арканы)
TAROT_CARDS = {
    "The Fool": {"meaning": "Начало, невинность, спонтанность", "reversed": "Безрассудство, риск"},
    "The Magician": {"meaning": "Проявление, сила воли, ресурсы", "reversed": "Манипуляция, неиспользованные таланты"},
    "The High Priestess": {"meaning": "Интуиция, тайны, подсознание", "reversed": "Скрытые мотивы, подавленная интуиция"},
    "The Empress": {"meaning": "Изобилие, природа, материнство", "reversed": "Зависимость, smothering"},
    "The Emperor": {"meaning": "Авторитет, структура, контроль", "reversed": "Тирания, жесткость"},
    # Добавьте остальные 73 карты здесь
}

class UserDB:
    def __init__(self):
        self.conn = sqlite3.connect('users.db', check_same_thread=False)
        self.create_table()
    
    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 10,
                referral_code TEXT,
                referred_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def get_user_balance(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            # Создаем нового пользователя с начальным балансом 10
            cursor.execute('INSERT INTO users (user_id, balance) VALUES (?, ?)', (user_id, 10))
            self.conn.commit()
            return 10
    
    def update_balance(self, user_id, amount):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        self.conn.commit()
    
    def set_balance(self, user_id, amount):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (amount, user_id))
        self.conn.commit()

# Инициализация базы данных
db = UserDB()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    
    if args:
        if args[0].startswith('balance_'):
            # Установка баланса (для админа)
            if str(user_id) == ADMIN_CHAT_ID:
                new_balance = int(args[0].split('_')[1])
                db.set_balance(user_id, new_balance)
                await update.message.reply_text(f"✅ Баланс установлен: {new_balance} вопросов")
                return
        
        elif args[0].startswith('ref_'):
            # Реферальная система
            referrer_id = int(args[0].split('_')[1])
            current_balance = db.get_user_balance(user_id)
            
            if current_balance == 10:  # Только для новых пользователей
                db.update_balance(user_id, 10)
                db.update_balance(referrer_id, 10)
                await update.message.reply_text("🎉 Вы и ваш друг получили по 10 бесплатных вопросов!")
    
    balance = db.get_user_balance(user_id)
    
    welcome_text = """
🔮 *Приветствую! Меня зовут Спу́тник.* 

Я мудрый советчик в мире Таро, готовый помочь вам найти ответы и прояснить ситуацию. 

✨ *Что я умею:*
• Делать расклады на ваши вопросы
• Толковать карты Таро
• Давать советы и направление

💫 *Просто напишите свой вопрос*, и я проведу для вас гадание.

Баланс: {} вопросов
    """.format(balance)
    
    keyboard = [
        [InlineKeyboardButton("💰 Купить вопросы", url="https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/")],
        [InlineKeyboardButton("📱 Открыть приложение", url="https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    balance = db.get_user_balance(user_id)
    
    # Проверяем, является ли сообщение вопросом для гадания
    is_tarot_question = any(word in user_message.lower() for word in [
        'карта', 'гадание', 'расклад', 'таро', 'будущее', 'предсказание',
        'что будет', 'узнать', 'погадай', 'судьба'
    ])
    
    if is_tarot_question:
        if balance <= 0:
            await update.message.reply_text(
                "❌ *Баланс закончился!*\n\n"
                "Пополните баланс, чтобы продолжить гадания: \n"
                "https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/\n\n"
                "💫 Или пригласите друзей и получите по 10 вопросов!",
                parse_mode='Markdown'
            )
            return
        
        # Уменьшаем баланс
        db.update_balance(user_id, -1)
        new_balance = balance - 1
        
        # Отправляем сообщение "думаю"
        thinking_msg = await update.message.reply_text("💭 *Хорошо, я понял ваш вопрос...*\n\n_Загружаю карты и прозрение..._ ✨", parse_mode='Markdown')
        
        try:
            # Генерируем ответ через GPT
            tarot_response = await generate_tarot_response(user_message, user_id)
            
            # Удаляем сообщение "думаю"
            await thinking_msg.delete()
            
            # Отправляем финальный ответ
            final_message = f"{tarot_response}\n\n🔮 *Осталось вопросов: {new_balance}*"
            await update.message.reply_text(final_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            await thinking_msg.delete()
            await update.message.reply_text("⚠️ *Произошла ошибка. Пожалуйста, попробуйте еще раз.*", parse_mode='Markdown')
            # Возвращаем списанный вопрос
            db.update_balance(user_id, 1)
    
    else:
        # Обычный разговор без списания баланса
        response = "💫 *Я здесь, чтобы помочь вам с гаданиями Таро!*\n\nЗадайте ваш вопрос, и я проведу расклад карт. Например: \"Что меня ждет в любви?\" или \"Какая карта описывает мою текущую ситуацию?\""
        await update.message.reply_text(response, parse_mode='Markdown')

async def generate_tarot_response(question: str, user_id: int) -> str:
    """Генерирует ответ через GPT с учетом Таро"""
    
    # Выбираем случайные карты для расклада
    num_cards = random.randint(1, 3)
    selected_cards = random.sample(list(TAROT_CARDS.items()), num_cards)
    
    cards_description = ""
    for card_name, card_info in selected_cards:
        position = "прямое" if random.random() > 0.3 else "перевернутое"
        meaning = card_info["meaning"] if position == "прямое" else card_info["reversed"]
        cards_description += f"• {card_name} ({position}): {meaning}\n"
    
    prompt = f"""
    Ты - мудрый таролог Спу́тник. Пользователь задал вопрос: "{question}"
    
    Выпавшие карты:
    {cards_description}
    
    Ответь на русском, следуя этим правилам:
    1. Будь внимательным, заботливым советчиком
    2. Объясни значение выпавших карт в контексте вопроса
    3. Дай мудрый совет (3-4 предложения)
    4. Используй эмодзи и жирный шрифт для заголовков
    5. Не предсказывай фатальное будущее, а давай пищу для размышлений
    6. Ответ должен быть не более 8 предложений
    7. Напомни, что Таро - инструмент для самопознания
    
    Тон: спокойный, мудрый, поддерживающий.
    """
    
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты мудрый таролог Спу́тник, который дает глубокие, но доступные толкования карт Таро."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # Fallback ответ если OpenAI не работает
        return f"""
✨ **Выпавшие карты:**\n{cards_description}\n
💫 **Мое толкование:** Карты указывают на важные аспекты в вашей ситуации. Сейчас время для размышлений и внимательного отношения к знакам вокруг.\n
🌙 **Совет:** Прислушайтесь к своей интуиции и не торопитесь с выводами. Помните, что Таро - это инструмент для самопознания, а не строгое предсказание будущего.
        """

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает текущий баланс"""
    user_id = update.effective_user.id
    balance = db.get_user_balance(user_id)
    
    await update.message.reply_text(
        f"💫 *Ваш текущий баланс:* {balance} вопросов\n\n"
        f"Приглашайте друзей и получайте бонусы! 🎁",
        parse_mode='Markdown'
    )

def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance_command))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    application.run_polling()
    print("Бот запущен!")

if __name__ == '__main__':
    main()