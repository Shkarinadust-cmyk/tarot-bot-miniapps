// Баланс пользователя
let userBalance = 7;
let selectedPackage = { amount: 300, price: 900 };

// Открытие модальных окон
function openPayment() {
    document.getElementById('paymentModal').style.display = 'block';
}

function openReferral() {
    document.getElementById('referralModal').style.display = 'block';
    // Генерация реферальной ссылки
    document.getElementById('referralLink').value = 'https://t.me/SputnikTarobot?start=ref_' + Math.random().toString(36).substr(2, 9);
}

function openAdvice() {
    const toggle = document.getElementById('adviceToggle');
    toggle.classList.toggle('active');
    
    const timeElement = document.getElementById('adviceTime');
    if (toggle.classList.contains('active')) {
        timeElement.textContent = '18:00 – 19:00';
    } else {
        timeElement.textContent = 'Отключено';
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Выбор пакета сообщений
function selectPackage(amount, price) {
    selectedPackage = { amount, price };
    
    // Убираем активный класс у всех опций
    document.querySelectorAll('.payment-option').forEach(option => {
        option.classList.remove('active');
    });
    
    // Добавляем активный класс к выбранной опции
    event.target.closest('.payment-option').classList.add('active');
}

// Обработка оплаты
function processPayment(method) {
    const paymentUrls = {
        100: 'https://yookassa.ru/my/i/aRWz8G2MdcMQ/l',
        200: 'https://yookassa.ru/my/i/aRW0Hp0pnJY4/l', 
        300: 'https://yookassa.ru/my/i/aRW0ONaTgvr4/l',
        500: 'https://yookassa.ru/my/i/aRW0UpykQRFm/l',
        1000: 'https://yookassa.ru/my/i/aRW0auBkhbht/l'
    };
    
    const url = paymentUrls[selectedPackage.amount];
    if (url) {
        window.open(url, '_blank');
        // Здесь будет интеграция с ЮКассой для подтверждения платежа
        alert('Переход к оплате... После оплаты баланс обновится автоматически.');
    }
}

// Копирование реферальной ссылки
function copyReferralLink() {
    const linkInput = document.getElementById('referralLink');
    linkInput.select();
    document.execCommand('copy');
    alert('Ссылка скопирована!');
}

// Поделиться реферальной ссылкой
function shareReferral() {
    const link = document.getElementById('referralLink').value;
    const text = `Привет! Попробуй этого удивительного бота Таро 🔮\n${link}\nМы оба получим по 10 бесплатных вопросов!`;
    
    if (navigator.share) {
        navigator.share({
            title: 'Аркана - Таро бот',
            text: text,
            url: link
        });
    } else {
        alert('Скопируйте ссылку и отправьте другу вручную: ' + link);
    }
}

// Закрытие модальных окон при клике вне их
window.onclick = function(event) {
    const modals = document.getElementsByClassName('modal');
    for (let modal of modals) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }
}

// Функции для нижнего меню
function openReviews() {
    window.open('https://t.me/your_reviews_channel', '_blank');
}

function openSupport() {
    window.open('https://t.me/your_support_channel', '_blank');
}

function openLegal() {
    alert('Здесь будет юридическая информация');
}

// Обновление баланса
function updateBalanceDisplay() {
    document.getElementById('balanceAmount').textContent = userBalance + ' сообщений';
}