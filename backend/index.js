const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(bodyParser.json());

// Храним баланс пользователей (в реальном проекте используй базу данных)
const userBalances = {};

// Маршрут для получения баланса
app.get('/api/balance/:userId', (req, res) => {
  const userId = req.params.userId;
  const balance = userBalances[userId] || 10; // Начальный баланс 10
  res.json({ balance });
});

// Маршрут для обновления баланса (после оплаты)
app.post('/api/balance/update', (req, res) => {
  const { userId, amount } = req.body;
  if (!userBalances[userId]) userBalances[userId] = 10;
  userBalances[userId] += amount;
  res.json({ success: true, newBalance: userBalances[userId] });
});

// Вебхук от ЮKassa для подтверждения оплаты
app.post('/api/payment/webhook', (req, res) => {
  const { object } = req.body;
  if (object.status === 'succeeded') {
    const userId = object.metadata.userId;
    const questions = object.metadata.questions;
    // Обновляем баланс
    if (!userBalances[userId]) userBalances[userId] = 10;
    userBalances[userId] += questions;
    console.log(`Пользователь ${userId} получил ${questions} вопросов`);
  }
  res.sendStatus(200);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Сервер запущен на порту ${PORT}`);
});