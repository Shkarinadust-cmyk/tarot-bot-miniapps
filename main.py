import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота из .env файла
BOT_TOKEN = os.getenv('BOT_TOKEN')

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Простой обработчик для health checks на Render"""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is alive!')
    
    def log_message(self, format, *args):
        """Отключаем стандартное логирование запросов"""
        return

def run_health_server():
    """Запускает HTTP сервер для health checks"""
    port = int(os.getenv('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Health check server running on port {port}")
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🔮 *Привет! Я бот Таро Спутник!*\n\n"
        "Бот успешно запущен на Render! 🎉\n"
        "Скоро добавлю функционал гадания.",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех текстовых сообщений"""
    await update.message.reply_text(
        "✨ Бот работает! Функционал Таро скоро будет добавлен.",
        parse_mode='Markdown'
    )

def main():
    """Основная функция запуска бота"""
    try:
        # Проверяем наличие токена
        if not BOT_TOKEN:
            logger.error("❌ BOT_TOKEN не найден! Убедись, что он установлен в переменных окружения.")
            return

        # Запускаем health server в отдельном потоке
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()

        # Создаем приложение бота
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("🤖 Бот запускается...")
        logger.info("🩺 Health check server запущен")
        
        # Запускаем бота
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        raise

if __name__ == '__main__':
    main()
