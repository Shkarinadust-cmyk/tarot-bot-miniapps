# 🔌 API Reference

## База данных

### Таблица: users
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 10,
    referral_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);