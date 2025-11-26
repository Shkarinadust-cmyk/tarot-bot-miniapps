// Конфигурация оплаты
const paymentConfig = {
    prices: {
        100: 300,
        200: 600,
        300: 900, 
        500: 1500,
        1000: 3000
    },
    urls: {
        100: 'https://yookassa.ru/my/i/aRWz8G2MdcMQ/l',
        200: 'https://yookassa.ru/my/i/aRW0Hp0pnJY4/l',
        300: 'https://yookassa.ru/my/i/aRW0ONaTgvr4/l',
        500: 'https://yookassa.ru/my/i/aRW0UpykQRFm/l',
        1000: 'https://yookassa.ru/my/i/aRW0auBkhbht/l'
    }
};

// Инициализация платежной системы
function initPaymentSystem() {
    console.log('💰 Payment system initialized');
}

// Выбор пакета вопросов
function selectPackage(questions, price) {
    const packages = document.querySelectorAll('.payment-option');
    packages.forEach(pkg => pkg.classList.remove('active'));
    
    event.currentTarget.classList.add('active');
    
    // Сохраняем выбранный пакет
    window.selectedPackage = {
        questions: questions,
        price: price
    };
    
    updatePaymentSummary(questions, price);
}

// Обновление информации о платеже
function updatePaymentSummary(questions, price) {
    const summaryElement = document.getElementById('paymentSummary');
    if (summaryElement) {
        summaryElement.innerHTML = `
            <strong>${questions} вопросов</strong><br>
            <span>${price} рублей</span>
        `;
    }
}

// Процесс оплаты
function processPayment(method) {
    if (!window.selectedPackage) {
        alert('❌ Выберите пакет вопросов');
        return;
    }
    
    const questions = window.selectedPackage.questions;
    const paymentUrl = paymentConfig.urls[questions];
    
    if (paymentUrl) {
        // Открываем страницу оплаты в новом окне
        const paymentWindow = window.open(paymentUrl, '_blank');
        
        if (paymentWindow) {
            // Начинаем отслеживание статуса платежа
            startPaymentTracking(questions);
        } else {
            alert('⚠️ Разрешите всплывающие окна для оплаты');
        }
    } else {
        alert('❌ Ошибка: ссылка оплаты не найдена');
    }
}

// Отслеживание статуса платежа
function startPaymentTracking(questions) {
    console.log(`🔄 Отслеживание платежа за ${questions} вопросов`);
    
    // Здесь будет логика опроса сервера о статусе платежа
    // Пока просто показываем сообщение
    setTimeout(() => {
        if (confirm('Оплата прошла успешно? Баланс обновится автоматически.')) {
            // Обновляем баланс (в реальности это сделает вебхук)
            updateUserBalance(questions);
        }
    }, 3000);
}

// Обновление баланса пользователя
function updateUserBalance(questions) {
    // В реальном приложении здесь будет запрос к API
    console.log(`✅ Баланс пополнен на ${questions} вопросов`);
    alert(`🎉 Баланс пополнен на ${questions} вопросов!`);
}

// Копирование реферальной ссылки
function copyReferralLink() {
    const linkInput = document.getElementById('referralLink');
    if (linkInput) {
        linkInput.select();
        linkInput.setSelectionRange(0, 99999);
        document.execCommand('copy');
        alert('✅ Ссылка скопирована!');
    }
}

// Поделиться ссылкой
function shareReferral() {
    const link = document.getElementById('referralLink').value;
    const shareText = `🔮 Привет! Попробуй удивительного бота Таро - Спу́тник!\n\n${link}\n\nМы оба получим по 10 бесплатных вопросов! ✨`;
    
    if (navigator.share) {
        navigator.share({
            title: 'Таро бот Спу́тник',
            text: shareText,
            url: link
        });
    } else {
        prompt('📤 Скопируй и отправь другу эту ссылку:', link);
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initPaymentSystem();
    console.log('🟢 Payment system ready');
});