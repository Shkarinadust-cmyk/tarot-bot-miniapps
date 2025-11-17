import requests
import sqlite3
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, PAYMENT_LINKS

class YooKassaPayment:
    def __init__(self):
        self.shop_id = YOOKASSA_SHOP_ID
        self.secret_key = YOOKASSA_SECRET_KEY
 
    def create_payment(self, user_id, amount, questions_count):
        """Создание платежа в ЮKassa"""
        return {
            "payment_url": PAYMENT_LINKS.get(questions_count),
            "amount": amount,
            "questions": questions_count
        }
 
    def verify_payment(self, payment_id):
        """Проверка статуса платежа"""
        # Здесь будет проверка через API ЮKassa
        return True  # временно всегда успех

def add_questions_to_user(user_id, questions_count):
    """Добавление вопросов пользователю"""
    conn = sqlite3.connect('tarot_bot.db')
    c = conn.cursor()
    c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?',
              (questions_count, user_id))
    conn.commit()
    conn.close()