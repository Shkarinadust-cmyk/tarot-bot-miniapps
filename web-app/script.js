// Инициализация Telegram Web App
let tg = window.Telegram.WebApp;

// Инициализация приложения
function initApp() {
    tg.expand();
    tg.enableClosingConfirmation();
    
    // Загружаем данные пользователя
    loadUserData();
    
    // Настраиваем переключатель совета дня
    const toggle = document.getElementById('adviceToggle');
    const timeSettings = document.getElementById('timeSettings');
    
    toggle.addEventListener('change', function() {
        timeSettings.style.display = this.checked ? 'block' : 'none';
    });
}

// Загрузка данных пользователя
function loadUserData() {
    const user = tg.initDataUnsafe?.user;
    if (user) {
        // Генерируем реферальную ссылку
        const referralLink = `https://t.me/SputnikTarobot?start=ref_${user.id}`;
        document.getElementById('referralLink').textContent = referralLink;
        
        // Здесь будет запрос к вашему API для получения баланса и друзей
        // updateBalance(user.id);
        // loadFriends(user.id);
    }
}

// Показать модальное окно оплаты
function showPayment() {
    document.getElementById('paymentModal').style.display = 'block';
}

// Закрыть модальное окно
function closeModal() {
    document.getElementById('paymentModal').style.display = 'none';
}

// Выбор пакета сообщений
let selectedPackage = 300;
function selectPackage(amount) {
    selectedPackage = amount;
    
    // Убираем активный класс у всех опций
    document.querySelectorAll('.payment-option').forEach(option => {
        option.classList.remove('active');
    });
    
    // Добавляем активный класс выбранной опции
    event.target.classList.add('active');
}

// Копирование реферальной ссылки
function copyLink() {
    const link = document.getElementById('referralLink').textContent;
    navigator.clipboard.writeText(link).then(() => {
        alert('Ссылка скопирована!');
    });
}

// Приглашение друзей
function inviteFriends() {
    const link = document.getElementById('referralLink').textContent;
    const message = `🔮 Привет! Попробуй моего бота для гадания на Таро - Спрutnik! Получи 10 бесплатных вопросов по моей ссылке: ${link}`;
    
    if (tg.isVersionAtLeast('6.1')) {
        tg.shareUrl(message, link);
    } else {
        navigator.clipboard.writeText(message).then(() => {
            alert('Сообщение скопировано! Отправьте его друзьям.');
        });
    }
}

// Сохранение настроек
function saveSettings() {
    const isEnabled = document.getElementById('adviceToggle').checked;
    const time = document.getElementById('adviceTime').value;
    const timezone = document.getElementById('timezone').value;
    
    // Здесь будет сохранение настроек через API
    alert('Настройки сохранены!');
    closeModal();
}

// Показать юридическую информацию
function showLegal() {
    alert('Здесь будет юридическая информация');
}

// Инициализация приложения при загрузке
document.addEventListener('DOMContentLoaded', initApp);