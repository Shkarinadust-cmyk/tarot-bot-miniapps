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
            balance INTEGER DEFAULT 10,  # 10 бесплатных вопросов
            referral_code TEXT,
            referred_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица платежей
    c.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            user_id INTEGER,
            questions_count INTEGER,
            amount INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных создана!")

def get_user_balance(user_id):
    """Получить баланс пользователя"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'tarot_bot.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            # Создаем нового пользователя
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)', 
                     (user_id, 10))  # 10 бесплатных вопросов
            conn.commit()
            conn.close()
            return 10
    except Exception as e:
        print(f"Ошибка получения баланса: {e}")
        return 0

def decrease_balance(user_id):
    """Уменьшить баланс на 1 вопрос"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'tarot_bot.db')
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('UPDATE users SET balance = balance - 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Ошибка уменьшения баланса: {e}")
        return False

if __name__ == '__main__':
    init_db()