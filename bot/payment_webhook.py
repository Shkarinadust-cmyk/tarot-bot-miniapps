import sqlite3
import logging
from flask import Flask, request, jsonify

logger = logging.getLogger(__name__)

def init_payment_db():
    """Инициализация базы для платежей"""
    conn = sqlite3.connect('payments.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            payment_id TEXT UNIQUE,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def process_yookassa_payment(payment_data):
    """Обработка платежа от ЮКассы"""
    try:
        payment_id = payment_data.get('object', {}).get('id')
        amount = payment_data.get('object', {}).get('amount', {}).get('value', 0)
        user_id = payment_data.get('object', {}).get('metadata', {}).get('user_id')
        status = payment_data.get('object', {}).get('status')
        
        if status == 'succeeded' and user_id and amount > 0:
            # Определяем количество вопросов по сумме
            questions_map = {
                300: 100,   # 300 руб = 100 вопросов
                600: 200,   # 600 руб = 200 вопросов
                900: 300,   # 900 руб = 300 вопросов
                1500: 500,  # 1500 руб = 500 вопросов
                3000: 1000  # 3000 руб = 1000 вопросов
            }
            
            questions = questions_map.get(amount, amount // 3)
            
            # Обновляем баланс пользователя
            conn = sqlite3.connect('users.db', check_same_thread=False)
            cursor = conn.cursor()
            
            # Получаем текущий баланс
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            current_balance = result[0] if result else 0
            
            # Обновляем баланс
            new_balance = current_balance + questions
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, balance) 
                VALUES (?, ?)
            ''', (user_id, new_balance))
            
            # Сохраняем информацию о платеже
            cursor.execute('''
                INSERT INTO payments (user_id, amount, payment_id, status)
                VALUES (?, ?, ?, ?)
            ''', (user_id, questions, payment_id, status))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Платеж обработан: user {user_id} +{questions} вопросов")
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки платежа: {e}")
        return False