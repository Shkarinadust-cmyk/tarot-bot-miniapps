import os
import logging
import sqlite3
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from tarot_logic import tarot_logic

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

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('tarot_bot.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Создаем таблицы в базе данных"""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                bonus_applied BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (referred_id) REFERENCES users (user_id)
            )
        ''')
        self.conn.commit()
    
    def add_user(self, user_id, username, referrer_id=None):
        """Добавляем пользователя в базу"""
        try:
            self.conn.execute(
                'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
                (user_id, username)
            )
            
            # Если есть реферер, добавляем запись в рефералы
            if referrer_id:
                self.conn.execute(
                    'INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?, ?)',
                    (referrer_id, user_id)
                )
                
                # Проверяем, не выдавали ли уже бонус
                cursor = self.conn.execute(
                    'SELECT bonus_applied FROM referrals WHERE referrer_id = ? AND referred_id = ?',
                    (referrer_id, user_id)
                )
                result = cursor.fetchone()
                
                if result and not result[0]:
                    # Начисляем бонусы обоим пользователям
                    self.conn.execute(
                        'UPDATE users SET balance = balance + 10 WHERE user_id IN (?, ?)',
                        (referrer_id, user_id)
                    )
                    # Отмечаем что бонус применен
                    self.conn.execute(
                        'UPDATE referrals SET bonus_applied = TRUE WHERE referrer_id = ? AND referred_id = ?',
                        (referrer_id, user_id)
                    )
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def get_balance(self, user_id):
        """Получаем баланс пользователя"""
        try:
            cursor = self.conn.execute(
                'SELECT balance FROM users WHERE user_id = ?', (user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0
    
    def use_question(self, user_id):
        """Используем один вопрос"""
        try:
            current_balance = self.get_balance(user_id)
            if current_balance <= 0:
                return 0
            
            new_balance = current_balance - 1
            self.conn.execute(
                'UPDATE users SET balance = ? WHERE user_id = ?',
                (new_balance, user_id)
            )
            self.conn.commit()
            return new_balance
        except Exception as e:
            logger.error(f"Error using question: {e}")
            return 0
    
    def add_questions(self, user_id, amount):
        """Добавляем вопросы пользователю"""
        try:
            self.conn.execute(
                'UPDATE users SET balance = balance + ? WHERE user_id = ?',
                (amount, user_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding questions: {e}")
            return False

class TarotBot:
    def __init__(self):
        self.db = Database()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Путник"
        
        # Проверяем есть ли реферальный код
        referrer_id = None
        if context.args:
            for arg in context.args:
                if arg.startswith('ref_'):
                    try:
                        referrer_id = int(arg[4:])
                        # Проверяем существует ли такой пользователь
                        if self.db.get_balance(referrer_id) is not None:
                            break
                    except ValueError:
                        continue
        
        # Регистрируем пользователя
        self.db.add_user(user_id, username, referrer_id)
        current_balance = self.db.get_balance(user_id)
        
        welcome_text = f"""
🌟 *Приветствую, {username}!* 🌟

Меня зовут *Спутник* — твой мудрый проводник в мире Таро. 

Я помогу тебе:
🔮 *Делать точные расклады*
💫 *Отвечать на твои вопросы*  
🌙 *Находить ясность и вдохновение*

Просто напиши свой вопрос, и мы начнем наше путешествие!

*Твой баланс:* {current_balance} вопросов
        """
        
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик всех текстовых сообщений"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        # Пропускаем простые приветствия без списания баланса
        if self.is_greeting(user_message):
            await update.message.reply_text(
                "🌟 *Привет! Я готов помочь тебе с раскладами Таро.*\n\n"
                "Просто задай свой вопрос о любви, работе, будущем или любой другой теме, "
                "и я проведу гадание с помощью карт Таро! ✨",
                parse_mode='Markdown'
            )
            return
        
        # Проверяем баланс
        balance = self.db.get_balance(user_id)
        
        if balance <= 0:
            await update.message.reply_text(
                "❌ *Баланс закончился!* \n\n"
                "Чтобы продолжить наше общение, пополни баланс вопросов:\n"
                "[💳 Купить вопросы](https://shkarinadust-cmyk.github.io/tarot-bot-miniapps/payment.html)\n\n"
                "*Или пригласи друзей и получи +10 вопросов каждому!* 👥",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            return
        
        # Показываем что бот "думает"
        thinking_msg = await update.message.reply_text("🔄 *Загружаю карты...*", parse_mode='Markdown')
        
        try:
            # Генерируем ответ от ИИ
            tarot_response = await tarot_logic.generate_tarot_response(user_message)
        except Exception as e:
            logger.error(f"Error generating tarot response: {e}")
            tarot_response = """
*🌀 Произошла магическая заминка...*

Карты временно притихли... Давай попробуем еще раз! 
Иногда картам требуется немного больше времени для раскрытия своей мудрости.

Напиши свой вопрос заново, и мы обязательно получим ответ! ✨
            """
        
        # Уменьшаем баланс
        new_balance = self.db.use_question(user_id)
        
        # Удаляем сообщение "думаю"
        await thinking_msg.delete()
        
        # Отправляем ответ
        response_text = f"{tarot_response}\n\n🔮 *Осталось вопросов:* {new_balance}"
        await update.message.reply_text(response_text, parse_mode='Markdown')

    def is_greeting(self, message: str) -> bool:
        """Проверяет, является ли сообщение простым приветствием"""
        greetings = [
            'привет', 'здравствуй', 'hello', 'hi', 'прив', 'начать', 
            'start', 'ку', 'салют', 'добрый', 'хай', 'здаров', 'здорово'
        ]
        message_lower = message.lower().strip()
        
        # Если сообщение слишком короткое
        if len(message_lower) < 3:
            return True
            
        # Проверяем совпадение с приветствиями
        for greeting in greetings:
            if greeting in message_lower:
                return True
                
        return False

    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для проверки баланса"""
        user_id = update.effective_user.id
        balance = self.db.get_balance(user_id)
        
        await update.message.reply_text(
            f"💫 *Твой текущий баланс:* {balance} вопросов\n\n"
            f"Пригласи друзей и получи +10 вопросов каждому! 👥",
            parse_mode='Markdown'
        )

    async def referral_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для получения реферальной ссылки"""
        user_id = update.effective_user.id
        referral_link = f"https://t.me/SputnikTarobot?start=ref_{user_id}"
        
        await update.message.reply_text(
            f"👥 *Пригласи друзей и получи бонусы!*\n\n"
            f"Дай эту ссылку друзьям:\n`{referral_link}`\n\n"
            f"Когда они зарегистрируются:\n"
            f"• Ты получишь *+10 вопросов*\n"
            f"• Друг получит *+10 вопросов*\n"
            f"• Вы сможете вместе исследовать мир Таро! ✨",
            parse_mode='Markdown'
        )

def run_health_server():
    """Запускает HTTP сервер для health checks"""
    port = int(os.getenv('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Health check server running on port {port}")
    server.serve_forever()

def main():
    """Основная функция запуска бота"""
    try:
        # Создаем приложение бота
        application = Application.builder().token(BOT_TOKEN).build()
        bot = TarotBot()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CommandHandler("balance", bot.balance_command))
        application.add_handler(CommandHandler("referral", bot.referral_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
        
        # Запускаем health server в отдельном потоке
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        
        logger.info("🤖 Бот запускается...")
        logger.info("🩺 Health check server запущен")
        
        # Запускаем бота
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == '__main__':
    main()