const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
require('dotenv').config();

const token = process.env.TELEGRAM_BOT_TOKEN;
const bot = new TelegramBot(token, { polling: true });
const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY;

// Приветственное сообщение
bot.onText(/\/start/, async (msg) => {
  const chatId = msg.chat.id;
  const userId = msg.from.id;
  
  // Проверяем реферальную ссылку
  const args = msg.text.split(' ');
  if (args[1] === 'balance_10') {
    // Сброс баланса на 10
    await axios.post('http://localhost:3000/api/balance/update', {
      userId,
      amount: 10
    });
  } else if (args[1] && args[1].startsWith('ref_')) {
    // Начисление 10 вопросов за реферала
    await axios.post('http://localhost:3000/api/balance/update', {
      userId,
      amount: 10
    });
  }

  const welcomeMsg = `🔮 *Приветствую, ${msg.from.first_name}!*\n\nМеня зовут *Спутник*, я твой мудрый советчик в мире Таро. 🌙\n\nЯ умею:\n• Делать расклады на ваши вопросы\n• Давать советы по картам\n• Помогать разобраться в ситуациях\n\n*Ваш начальный баланс:* 10 вопросов\n\nНапишите свой вопрос, и мы начнем наше путешествие по картам! ✨`;
  
  bot.sendMessage(chatId, welcomeMsg, { parse_mode: 'Markdown' });
});

// Обработка всех сообщений
bot.on('message', async (msg) => {
  if (msg.text.startsWith('/')) return;
  
  const chatId = msg.chat.id;
  const userId = msg.from.id;
  const userText = msg.text.toLowerCase();
  
  // Проверяем баланс
  const balanceRes = await axios.get(`http://localhost:3000/api/balance/${userId}`);
  const balance = balanceRes.data.balance;
  
  // Если есть слова "карта", "таро", "расклад", "гадание" - считаем вопросом
  const isTarotQuestion = /карт|таро|расклад|гадан|предсказ|будущ|завтра|сегод|вчера|ситуац|отношен|работ|деньг|любов|здоров/.test(userText);
  
  if (!isTarotQuestion) {
    bot.sendMessage(chatId, "Привет! 👋 Задайте вопрос, связанный с картами Таро, и я помогу вам с раскладом! ✨");
    return;
  }
  
  if (balance <= 0) {
    bot.sendMessage(chatId, `❌ *Баланс закончился!*\n\nПополните вопросы через приложение:\nhttps://shkarinadust-cmyk.github.io/tarot-bot-miniapps/`, { parse_mode: 'Markdown' });
    return;
  }
  
  // Отправляем "типинг" (печатает...)
  bot.sendChatAction(chatId, 'typing');
  
  // Запрашиваем ответ у AI
  const aiResponse = await getAIResponse(userText, balance);
  
  // Отправляем ответ
  bot.sendMessage(chatId, aiResponse, { parse_mode: 'Markdown' });
  
  // Уменьшаем баланс на 1
  await axios.post('http://localhost:3000/api/balance/update', {
    userId,
    amount: -1
  });
});

// Функция запроса к DeepSeek
async function getAIResponse(question, balance) {
  try {
    const response = await axios.post('https://api.deepseek.com/v1/chat/completions', {
      model: 'deepseek-chat',
      messages: [{
        role: 'system',
        content: `Ты - мудрый таролог "Спутник". Ты используешь классическую колоду Уэйта. Отвечай на русском, используй эмодзи и жирный шрифт. Структура ответа: 1) Понимание вопроса, 2) Расклад (название карты и положение), 3) Толкование, 4) Итоговый совет. Не больше 10 предложений. Текущий баланс пользователя: ${balance} вопросов. В конце всегда пиши "🔮 Осталось вопросов: ${balance-1}"`
      }, {
        role: 'user',
        content: question
      }],
      max_tokens: 500,
      temperature: 0.7
    }, {
      headers: {
        'Authorization': `Bearer ${DEEPSEEK_API_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data.choices[0].message.content;
  } catch (error) {
    console.error('Ошибка DeepSeek:', error);
    return `✨ *Карта: Шут* (прямое положение)\n\nЭта карта говорит о новых начинаниях и доверии к пути. В вашей ситуации важно сохранить легкость и открыться новым возможностям.\n\n*Совет:* Позвольте себе сделать шаг в неизвестность — это может привести к неожиданным радостям!\n\n🔮 Осталось вопросов: ${balance-1}`;
  }
}