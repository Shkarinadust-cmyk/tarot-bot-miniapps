import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3
from database import db
import requests
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "8355095598:AAGi48QWU-4e66ZTR2qMYU6aiK-Py1TxjWU"

# Карты Таро
TAROT_CARDS = {
    "Старшие Арканы": [
        "🃏 Шут", "🧙‍♂️ Маг", "🔮 Жрица", "👑 Императрица", "🏛️ Император",
        "⛪ Иерофант", "💑 Влюбленные", "🐎 Колесница", "💪 Сила", "🧘‍♂️ Отшельник",
        "🔄 Колесо Фортуны", "⚖️ Правосудие", "🙏 Повешенный", "💀 Смерть",
        "😇 Умеренность", "😈 Дьявол", "⚡ Башня", "⭐ Звезда", "🌙 Луна",
        "☀️ Солнце", "🎭 Суд", "🌍 Мир"
    ],
    "Младшие Арканы": [
        "✨ Туз Жезлов", "2️⃣ Двойка Жезлов", "3️⃣ Тройка Жезлов", 
        "4️⃣ Четверка Жезлов", "5️⃣ Пятерка Жезлов", "6️⃣ Шестерка Жезлов",
        "7️⃣ Семерка Жезлов", "8️⃣ Восьмерка Жезлов", "9️⃣ Девятка Жезлов",
        "🔟 Десятка Жезлов", "💂‍♂️ Паж Жезлов", "♊ Рыцарь Жезлов",
        "👸 Королева Жезлов", "🤴 Король Жезлов"
    ]
}

class TarotBot:
    def __init__(self):
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        args = context.args
        
        if args:
            if args[0].startswith('ref_'):
                referrer_id = int(args[0].split('_')[1])
                # Начисляем бонусы обоим пользователям
                db.update_balance(user_id, 10)
                db.update_balance(referrer_id, 10)
                await update.message.reply_text("🎉 Вам начислено 10 бесплатных вопросов за регистрацию по ссылке друга!")
            elif args[0] == "balance_10":
                db.update_balance(user_id, 10)
                await update.message.reply_text("✅ Баланс пополнен на 10 вопросов!")
        
        db.create_user(user_id)
        balance = db.get_user_balance(user_id)
        
        welcome_text = f"""
🌟 *Добро пожаловать, {update.effective_user.first_name}!* 🌟

Меня зовут **Спутник** 🧙‍♂️, и я готов помочь вам заглянуть в мир Таро. 

Я умею:
🔮 Делать расклады на ваши вопросы
💫 Давать советы и подсказки
🌙 Помогать разобраться в сложных ситуациях

Просто напишите свой вопрос, и я проведу расклад!

✨ *Ваш баланс: {balance} вопросов* ✨
        """
        
        keyboard = [
            [InlineKeyboardButton("💳 Купить вопросы", url="https://shkarinadust-cmyk.github.io/tarot-bot-miniapp/")],
            [InlineKeyboardButton("👥 Пригласить друзей", callback_data="invite")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    def generate_tarot_response(self, question, user_id):
        """Генерация ответа от ИИ для Таро"""
        balance = db.get_user_balance(user_id)
        
        if balance <= 0:
            return "❌ Баланс закончился! Пополните: https://shkarinadust-cmyk.github.io/tarot-bot-miniapp/"
        
        # Выбираем случайные карты для расклада
        spread_type = random.choice(["Расклад на ситуацию", "Расклад на день", "Расклад на отношения"])
        cards = random.sample(TAROT_CARDS["Старшие Арканы"] + TAROT_CARDS["Младшие Арканы"], 3)
        positions = ["Прямое", "Перевернутое", "Прямое"]
        
        # Формируем ответ
        response = f"""
🃏 *Запрос:* {question}
🔮 *Расклад:* {spread_type}

*Выпавшие карты:*
1️⃣ **{cards[0]}** - {positions[0]}
2️⃣ **{cards[1]}** - {positions[1]}  
3️⃣ **{cards[2]}** - {positions[2]}

*Интерпретация:*
Карты показывают, что вас ждут интересные события! {cards[0]} говорит о новых возможностях, {cards[1]} указывает на важные решения, а {cards[2]} символизирует гармонию.

*Совет:* Доверьтесь своей интуиции и будьте открыты к переменам! 🌟

💫 Хотите разобрать ситуацию глубже?
        """
        
        # Обновляем баланс
        db.update_balance(user_id, -1)
        new_balance = db.get_user_balance(user_id)
        response += f"\n🔮 *Осталось вопросов: {new_balance}*"
        
        return response
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Игнорируем приветствия и простые сообщения
        simple_phrases = ["привет", "здравствуй", "hi", "hello", "start", "/start"]
        if message_text.lower() in simple_phrases:
            balance = db.get_user_balance(user_id)
            await update.message.reply_text(f"✨ Привет! Готов помочь с раскладом Таро. Ваш баланс: {balance} вопросов")
            return
        
        # Показываем "типинг"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Генерируем ответ
        response = self.generate_tarot_response(message_text, user_id)
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    def run(self):
        self.app.run_polling()

if __name__ == "__main__":
    bot = TarotBot()
    bot.run()