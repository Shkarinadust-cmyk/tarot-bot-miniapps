import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('tarot_bot.db', check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 10
            )
        ''')
        self.conn.commit()

    def add_user(self, user_id, username):
        self.conn.execute(
            'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
            (user_id, username)
        )
        self.conn.commit()

    def get_balance(self, user_id):
        cursor = self.conn.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 0

    def use_question(self, user_id):
        balance = self.get_balance(user_id)
        if balance > 0:
            new_balance = balance - 1
            self.conn.execute(
                'UPDATE users SET balance = ? WHERE user_id = ?',
                (new_balance, user_id)
            )
            self.conn.commit()
            return new_balance
        return 0
