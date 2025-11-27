import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_health_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Health server running on port {port}")
    server.serve_forever()

async def start(update, context):
    await update.message.reply_text('Привет! Я бот Таро. Задай мне вопрос.')

async def handle_message(update, context):
    await update.message.reply_text('Пока я учусь...')

def main():
    # Запускаем health server в фоне
    thread = threading.Thread(target=run_health_server, daemon=True)
    thread.start()

    # Создаем приложение бота
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
