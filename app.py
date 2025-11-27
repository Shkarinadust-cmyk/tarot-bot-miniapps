import os
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

app = Flask(__name__)

# Вставьте сюда ваш токен. На Render.com его нужно будет добавить в переменные окружения.
BOT_TOKEN = os.getenv('BOT_TOKEN', '8355095598:AAGi48QWU-4e66ZTR2qMYU6aiK-Py1TxjWU')

# Создаем приложение бота один раз при запуске
application = Application.builder().token(BOT_TOKEN).build()

# Добавляем обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🔮 Бот успешно запущен на Render! Задайте ваш вопрос.')

application.add_handler(CommandHandler("start", start))

# Маршрут для вебхука от Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(), application.bot)
    application.update_queue.put(update)
    return 'ok', 200

# Маршрут для главной страницы (для проверки работы)
@app.route('/')
def index():
    return 'Бот работает!'

# Инициализируем бота при старте приложения
if __name__ == '__main__':
    # Запускаем бота в режиме вебхука
    application.run_webhook(
        listen='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        url_path='/webhook',
        webhook_url='https://tarot-bot-miniapps.onrender.com/webhook'
    )
