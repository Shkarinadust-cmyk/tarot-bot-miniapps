import sqlite3
import os

def init_db():
    """Инициализация базы данных"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'tarot_bot.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 3,
            referral_code TEXT,
            referred_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована!")

if __name__ == '__main__':
    init_db()