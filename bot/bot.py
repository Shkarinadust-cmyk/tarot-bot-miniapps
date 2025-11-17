import logging
import os
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен вашего бота
BOT_TOKEN = "8355095598:AAGi48QWU-4e66ZTR2qMYU6aiK-Py1TxjWU"

# Импортируем ИИ и базу данных
from ai_tarot import tarot_ai
import sys
sys.path.append('..')
from backend.database import get_user_balance, decrease_balance

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    # Регистрируем пользователя (баланс 10 вопросов)
    balance = get_user_balance(user.id)
    
    # Создаем кнопку для мини-приложения
    keyboard = [
        [InlineKeyboardButton("📱 Открыть приложение", web_app={"url": "https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/frontend/"})]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"Приветствую, {user.first_name}! 👋\n\n"
        f"Меня зовут **Спутник**, и я готов помочь вам с картами Таро.\n\n"
        f"✨ **У вас есть вопросы для раскладов** ✨\n\n"
        f"Я умею:\n"
        f"• Делать **персональные расклады** на ваши вопросы\n"
        f"• Давать **глубокие трактовки** карт\n" 
        f"• Подбирать карты **по тематике** вашего вопроса\n"
        f"• Предлагать **бесплатную карту дня** (/card)\n\n"
        f"Просто напишите свой вопрос, и я сделаю для вас уникальный расклад! 🔮\n\n"
        f"💫 *Чтобы пополнить вопросы, нажмите кнопку ниже:*"
    )
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

# Команда /balance
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    # Создаем кнопку для мини-приложения
    keyboard = [
        [InlineKeyboardButton("💳 Пополнить вопросы", web_app={"url": "https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/frontend/"})]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    balance_text = (
        f"💫 **Проверить баланс вопросов и пополнить его можно в нашем мини-приложении:**\n\n"
        f"Нажмите кнопку ниже чтобы открыть:"
    )
    
    await update.message.reply_text(balance_text, parse_mode='Markdown', reply_markup=reply_markup)

# Команда /card
async def daily_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Карта дня"""
    card_reading = tarot_ai.get_daily_card()
    await update.message.reply_text(card_reading, parse_mode='Markdown')

# Обработка обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user = update.message.from_user
    
    # Игнорируем короткие ответы типа "Да", "Нет"
    if user_message.lower() in ['да', 'нет', 'ок', 'хорошо', 'спасибо', 'понятно']:
        await update.message.reply_text(
            "💫 Задайте, пожалуйста, конкретный вопрос для расклада!\n\n"
            "Например:\n"
            "• «Что меня ждет в любви до конца года?»\n" 
            "• «Как сложится моя карьера?»\n"
            "• «Стоит ли начинать новый проект?»\n"
            "• «Что думает обо мне этот человек?»\n\n"
            "Я сделаю для вас персональный расклад из 3 карт! 🔮",
            parse_mode='Markdown'
        )
        return
    
    # Проверяем баланс (но не показываем пользователю)
    balance = get_user_balance(user.id)
    
    if balance <= 0:
        # Создаем кнопку для пополнения
        keyboard = [
            [InlineKeyboardButton("💳 Пополнить вопросы", web_app={"url": "https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/frontend/"})]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ **Для нового расклада необходимо пополнить вопросы**\n\n"
            "Нажмите кнопку ниже чтобы открыть приложение:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return
    
    # Показываем фразу "думаю"
    thinking_message = await update.message.reply_text(
        f"{tarot_ai.get_thinking_phrase()}",
        parse_mode='Markdown'
    )
    
    # Имитируем "думание"
    await update.message.reply_chat_action(action='typing')
    time.sleep(2)
    
    # Удаляем сообщение "думаю"
    await thinking_message.delete()
    
    # Используем ПРОДВИНУТЫЙ ИИ для создания расклада
    answer = tarot_ai.create_intelligent_reading(user_message)
    
    # Отправляем текстовый расклад
    await update.message.reply_text(answer, parse_mode='Markdown')
    
    # Уменьшаем баланс (не сообщаем пользователю)
    decrease_balance(user.id)

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
    print("✅ Профессиональный ИИ Таро: готов к работе")
    print("📱 Добавлены кнопки для мини-приложения")
    print("💫 10 бесплатных вопросов для каждого пользователя")
    print("🎴 Ожидаем вопросы...")
    
    application.run_polling()
    print("✅ Бот работает!")

if __name__ == '__main__':
    main()