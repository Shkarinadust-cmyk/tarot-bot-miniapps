// Получение баланса с сервера
async function updateBalance() {
    // В реальном проекте здесь будет запрос к API
    // const userId = localStorage.getItem('userId');
    // const response = await fetch(`https://ваш-сервер/api/balance/${userId}`);
    // const data = await response.json();
    // document.getElementById('balanceCount').textContent = data.balance;
    
    // Временный пример
    document.getElementById('balanceCount').textContent = localStorage.getItem('balance') || 10;
}

// Открытие окна оплаты
function openPayment() {
    document.getElementById('paymentModal').style.display = 'block';
}

function closePayment() {
    document.getElementById('paymentModal').style.display = 'none';
}

// Приглашение друзей
function inviteFriend() {
    const userId = localStorage.getItem('userId') || generateUserId();
    const inviteLink = `https://t.me/SputnikTarobot?start=ref_${userId}`;
    
    if (navigator.share) {
        navigator.share({
            title: 'Таро Бот Спутник',
            text: 'Привет! Попробуй удивительного Таро-бота! 🔮 Получи 10 бесплатных вопросов по моей ссылке:',
            url: inviteLink
        });
    } else {
        navigator.clipboard.writeText(inviteLink);
        alert('Ссылка скопирована! Отправь её другу. За каждого друга вы получите по 10 вопросов!');
    }
}

function generateUserId() {
    return 'user_' + Math.random().toString(36).substr(2, 9);
}

// Открытие документов
function openDocument(type) {
    const docs = {
        terms: 'Пользовательское соглашение текст...',
        privacy: 'Политика конфиденциальности текст...'
    };
    alert(docs[type]);
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    // Генерируем ID пользователя если нет
    if (!localStorage.getItem('userId')) {
        localStorage.setItem('userId', generateUserId());
    }
    
    updateBalance();
    closePayment();
});