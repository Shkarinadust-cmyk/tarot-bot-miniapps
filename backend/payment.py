import sqlite3
from config import PAYMENT_LINKS, DATABASE_PATH

class PaymentManager:
    def __init__(self):
        self.payment_links = PAYMENT_LINKS
    
    def create_payment(self, user_id, questions_count):
        """Создание платежа"""
        if questions_count not in self.payment_links:
            return None
            
        # Сохраняем в базу pending платеж
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        
        # Генерируем ID платежа
        payment_id = f"pay_{user_id}_{questions_count}_{int(time.time())}"
        
        c.execute('''
            INSERT INTO payments (payment_id, user_id, questions_count, status) 
            VALUES (?, ?, ?, 'pending')
        ''', (payment_id, user_id, questions_count))
        
        conn.commit()
        conn.close()
        
        return {
            'payment_url': self.payment_links[questions_count],
            'payment_id': payment_id
        }
    
    def confirm_payment(self, payment_id):
        """Подтверждение платежа"""
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        
        # Находим платеж
        c.execute('SELECT user_id, questions_count FROM payments WHERE payment_id = ?', (payment_id,))
        payment = c.fetchone()
        
        if payment:
            user_id, questions_count = payment
            
            # Обновляем баланс пользователя
            c.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', 
                     (questions_count, user_id))
            
            # Помечаем платеж как выполненный
            c.execute('UPDATE payments SET status = "completed" WHERE payment_id = ?', (payment_id,))
            
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False

# Создаем экземпляр менеджера платежей
payment_manager = PaymentManager()