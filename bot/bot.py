import logging
import sqlite3
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен вашего бота
BOT_TOKEN = "8355095598:AAGi48QWU-4e66ZTR2qMYU6aiK-Py1TxjWU"

# Путь к базе данных
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'tarot_bot.db')

class TarotAI:
    """Простой ИИ для Таро"""
    def __init__(self):
        self.cards = {
            "СИЛА": "Внутренняя сила, уверенность, преодоление препятствий. Вы обладаете всеми ресурсами для успеха!",
            "ШАЛУН": "Новые начинания, невинность, спонтанность. Не бойтесь начинать что-то новое!",
            "ИМПЕРАТРИЦА": "Красота, изобилие, творчество. Время творить и наслаждаться жизнью!",
            "ИМПЕРАТОР": "Власть, структура, контроль. Возьмите ситуацию под свой контроль!",
            "ЖРЕЦ": "Духовность, интуиция, высшее знание. Доверяйте своей интуиции!",
            "ВЛЮБЛЕННЫЕ": "Любовь, гармония, партнерство. Важны отношения и выбор сердца!",
            "КОЛЕСНИЦА": "Движение, прогресс, воля. Продолжайте движение вперед!",
            "ПРАВОСУДИЕ": "Справедливость, правда, карма. Все встанет на свои места!",
            "ОТШЕЛЬНИК": "Самоанализ, уединение, внутренняя мудрость. Время для размышлений!",
            "КОЛЕСО ФОРТУНЫ": "Судьба, удача, циклы. Удача на вашей стороне!",
            "МИР": "Завершение, успех, гармония. Все идет по плану!",
            "СОЛНЦЕ": "Радость, успех, оптимизм. Яркие перспективы впереди!",
            "ЛУНА": "Тайны, интуиция, подсознание. Прислушайтесь к внутреннему голосу!"
        }
    
    def get_daily_card(self):
        """Получить карту дня"""
        import random
        card = random.choice(list(self.cards.keys()))
        return f"🎴 **Карта дня: {card}**\n\n{self.cards[card]}"
    
    def answer_question(self, question):
        """Ответ на вопрос пользователя"""
        import random
        
        # Анализируем вопрос (простая логика)
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['любовь', 'отношен', 'сердц', 'чувств']):
            cards = ["ВЛЮБЛЕННЫЕ", "ИМПЕРАТРИЦА", "СОЛНЦЕ"]
        elif any(word in question_lower for word in ['работ', 'карьер', 'деньг', 'финанс']):
            cards = ["ИМПЕРАТОР", "КОЛЕСНИЦА", "МИР"]
        elif any(word in question_lower for word in ['здоров', 'самочувств', 'энерг']):
            cards = ["СИЛА", "СОЛНЦЕ", "МИР"]
        elif any(word in question_lower for word in ['будущ', 'судьб', 'завтра']):
            cards = ["КОЛЕСО ФОРТУНЫ", "ЛУНА", "ШАЛУН"]
        else:
            cards = random.sample(list(self.cards.keys()), 3)
        
        reading = f"🔮 **Ваш вопрос:** \"{question}\"\n\n"
        reading += "**Расклад на три карты:**\n\n"
        
        for i, card in enumerate(cards, 1):
            reading += f"{i}. **{card}** - {self.cards[card]}\n\n"
        
        reading += "---\n"
        reading += "Хотите более глубокий расклад? Просто задайте следующий вопрос! ✨"
        
        return reading

# Создаем экземпляр ИИ
tarot_ai = TarotAI()

def get_user_balance(user_id):
    """Получить баланс пользователя"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            # Создаем нового пользователя
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()
            c.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)', 
                     (user_id, 3))  # Дарим 3 бесплатных вопроса
            conn.commit()
            conn.close()
            return 3
    except Exception as e:
        logger.error(f"Ошибка получения баланса: {e}")
        return 0

def decrease_balance(user_id):
    """Уменьшить баланс на 1 вопрос"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('UPDATE users SET balance = balance - 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка уменьшения баланса: {e}")
        return False

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    # Регистрируем пользователя или получаем баланс
    balance = get_user_balance(user.id)
    
    welcome_text = (
        f"Приветствую, {user.first_name}! 👋\n\n"
        f"Меня зовут **Спутник**, и я готов помочь вам с картами Таро.\n\n"
        f"✨ **Ваш баланс:** {balance} вопросов\n\n"
        f"Я умею:\n"
        f"• Делать расклады на ваши вопросы\n"
        f"• Давать советы по картам Таро\n"
        f"• Помогать в сложных ситуациях\n\n"
        f"Просто напишите свой вопрос, и мы начнем волшебное путешествие! 🔮\n\n"
        f"💫 *Чтобы пополнить баланс, используйте наше мини-приложение:*\n"
        f"https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/frontend/"
    )
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

# Команда /balance
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    balance = get_user_balance(user.id)
    
    balance_text = (
        f"💫 **Ваш баланс:** {balance} вопросов\n\n"
        f"Пополнить баланс можно в нашем мини-приложении:\n"
        f"https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/frontend/"
    )
    
    await update.message.reply_text(balance_text, parse_mode='Markdown')

# Команда /card
async def daily_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Карта дня"""
    card_reading = tarot_ai.get_daily_card()
    await update.message.reply_text(card_reading, parse_mode='Markdown')

# Обработка обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user = update.message.from_user
    
    # Проверяем баланс
    balance = get_user_balance(user.id)
    
    if balance <= 0:
        await update.message.reply_text(
            "❌ **У вас закончились вопросы!**\n\n"
            "Чтобы продолжить наше волшебное путешествие, пополните баланс:\n\n"
            "💫 *Мини-приложение для пополнения:*\n"
            "https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/frontend/\n\n"
            "После пополнения возвращайтесь за новыми раскладами! 🔮",
            parse_mode='Markdown'
        )
        return
    
    # Используем ИИ для ответа
    answer = tarot_ai.answer_question(user_message)
    
    # Отправляем ответ
    await update.message.reply_text(answer, parse_mode='Markdown')
    
    # Уменьшаем баланс
    if decrease_balance(user.id):
        new_balance = balance - 1
        await update.message.reply_text(
            f"💫 Осталось вопросов: {new_balance}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "⚠️ Произошла ошибка при списании вопроса. Попробуйте еще раз.",
            parse_mode='Markdown'
        )

# Ошибки
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f'Update {update} caused error {context.error}')

# Запуск бота
def main():
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("card", daily_card))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Обработчик ошибок
    application.add_error_handler(error)
    
    # Запускаем бота
    print("🤖 Бот запускается...")
    print("✅ База данных: проверка баланса работает")
    print("🔮 ИИ Таро: готов к работе")
    print("💫 Ожидаем сообщения...")
    
    application.run_polling()
    print("✅ Бот работает!")

if __name__ == '__main__':
    main()