import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'tarot_bot.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 10,
            referrer_id INTEGER,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cur.fetchone()
    conn.close()
    if user:
        return {'user_id': user[0], 'balance': user[1], 'referrer_id': user[2], 'registration_date': user[3]}
    else:
        return None

def create_user(user_id, referrer_id=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO users (user_id, balance, referrer_id) VALUES (?, 10, ?)', (user_id, referrer_id))
    conn.commit()
    conn.close()

def update_balance(user_id, new_balance):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
    conn.commit()
    conn.close()

def add_balance(user_id, amount):
    user = get_user(user_id)
    if user:
        new_balance = user['balance'] + amount
        update_balance(user_id, new_balance)
        return new_balance
    else:
        create_user(user_id)
        return 10 + amount