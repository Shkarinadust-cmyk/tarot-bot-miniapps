import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен вашего бота
BOT_TOKEN = "8355095598:AAGi48QWU-4e66ZTR2qMYU6aiK-Py1TxjWU"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(
        f"Приветствую, {user.first_name}! 👋\n"
        "Меня зовут Спутник, и я готов помочь вам с картами Таро.\n\n"
        "Я умею делать расклады и отвечать на ваши вопросы по картам Таро.\n\n"
        "Напишите свой вопрос, и мы начнем волшебное путешествие! 🔮"
    )

# Обработка обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user = update.message.from_user
    
    # Временный ответ (потом заменим на ИИ)
    await update.message.reply_text(
        f"🔮 Ваш вопрос: \"{user_message}\"\n\n"
        "Карта дня: **СИЛА**\n"
        "Эта карта говорит о внутренней силе и уверенности. "
        "Завтра вас ждут позитивные изменения!\n\n"
        "Хотите сделать полный расклад для более детального ответа?"
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Обработчик ошибок
    application.add_error_handler(error)
    
    # Запускаем бота
    print("🤖 Бот запускается...")
    application.run_polling()
    print("✅ Бот работает!")

if __name__ == '__main__':
    main()