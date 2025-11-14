from flask import Flask, request, jsonify
import sqlite3
import json
import os

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('tarot_bot.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            referral_code TEXT,
            referred_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            user_id INTEGER,
            amount INTEGER,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных создана!")

@app.route('/')
def home():
    return "🚀 Backend для Таро бота работает!"

@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = sqlite3.connect('tarot_bot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return jsonify({
            'user_id': user[0],
            'balance': user[1],
            'referral_code': user[2]
        })
    return jsonify({'error': 'User not found'}), 404

if __name__ == '__main__':
    init_db()
    print("🌐 Сервер запускается на http://localhost:5000")
    app.run(debug=True, port=5000)