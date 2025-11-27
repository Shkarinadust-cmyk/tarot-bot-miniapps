import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Проверяем токен
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ ERROR: BOT_TOKEN not found!")
    exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"🔮 *Приветствую, {user.first_name}!*\n\n"
        "Я *Спутник* - твой проводник в мире Таро! 🌙\n\n"
        "Задай мне вопрос, и я сделаю расклад на картах Таро!\n"
        "Например: *«Что меня ждет сегодня?»* или *«Стоит ли мне менять работу?»*\n\n"
        "Я готов к работе! ✨",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех сообщений"""
    user_message = update.message.text
    
    # Простой ответ пока не настроен полноценный функционал Таро
    await update.message.reply_text(
        f"✨ *Твой вопрос:* \"{user_message}\"\n\n"
        "Сейчас я настраиваю систему гадания... 🔮\n"
        "Скоро я смогу делать настоящие расклады Таро!\n\n"
        "А пока проверь, готов ли ты получить ответ от карт? 🌙",
        parse_mode='Markdown'
    )

def main():
    """Основная функция запуска бота"""
    try:
        # Создаем приложение бота
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("🤖 Бот запускается...")
        logger.info(f"✅ Токен: {'Установлен' if BOT_TOKEN else 'НЕ УСТАНОВЛЕН!'}")
        
        # Запускаем бота
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        exit(1)

if __name__ == '__main__':
    main()
