// Основные функции приложения
function openPayment() {
    window.location.href = 'payment.html';
}

function openReferral() {
    window.location.href = 'referral.html';
}

function openAdviceSettings() {
    // Создаем модальное окно для настроек совета дня
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;
    
    modal.innerHTML = `
        <div style="
            background: linear-gradient(135deg, #8B4513 0%, #A0522D 100%);
            padding: 20px;
            border-radius: 15px;
            width: 90%;
            max-width: 400px;
            border: 2px solid #FFD700;
        ">
            <h3 style="color: #FFD700; margin-bottom: 20px; text-align: center;">⚙️ Настройка совета дня</h3>
            
            <div style="margin: 15px 0;">
                <label style="display: block; margin-bottom: 8px;">🕐 Время получения:</label>
                <select style="width: 100%; padding: 10px; border-radius: 8px; background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.3);">
                    <option value="morning">Утро (08:00-09:00)</option>
                    <option value="afternoon">День (12:00-13:00)</option>
                    <option value="evening" selected>Вечер (18:00-19:00)</option>
                    <option value="night">Ночь (22:00-23:00)</option>
                </select>
            </div>
            
            <div style="margin: 15px 0;">
                <label style="display: flex; align-items: center; gap: 10px;">
                    <input type="checkbox" checked>
                    <span>Включить ежедневные советы</span>
                </label>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button onclick="closeModal()" style="
                    flex: 1;
                    padding: 12px;
                    background: rgba(255,255,255,0.2);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                ">Отмена</button>
                <button onclick="saveAdviceSettings()" style="
                    flex: 1;
                    padding: 12px;
                    background: #FFD700;
                    color: #8B4513;
                    border: none;
                    border-radius: 8px;
                    font-weight: bold;
                    cursor: pointer;
                ">💾 Сохранить</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function closeModal() {
    const modal = document.querySelector('div[style*="position: fixed"]');
    if (modal) {
        modal.remove();
    }
}

function saveAdviceSettings() {
    alert('✅ Настройки совета дня сохранены!');
    closeModal();
}

function openLegal() {
    // Создаем модальное окно для юридической информации
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        overflow-y: auto;
        padding: 20px;
    `;
    
    modal.innerHTML = `
        <div style="
            background: linear-gradient(135deg, #8B4513 0%, #A0522D 100%);
            padding: 20px;
            border-radius: 15px;
            width: 90%;
            max-width: 400px;
            max-height: 80vh;
            overflow-y: auto;
            border: 2px solid #FFD700;
        ">
            <h3 style="color: #FFD700; margin-bottom: 20px; text-align: center;">📄 Юридическая информация</h3>
            
            <div style="margin-bottom: 20px;">
                <h4 style="color: #FFD700; margin-bottom: 10px;">📝 Пользовательское соглашение</h4>
                <p style="font-size: 14px; line-height: 1.4; opacity: 0.9;">
                    Используя это приложение, вы соглашаетесь с условиями предоставления услуг. 
                    Гадание на картах Таро предоставляется в развлекательных целях.
                </p>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h4 style="color: #FFD700; margin-bottom: 10px;">🛡️ Политика конфиденциальности</h4>
                <p style="font-size: 14px; line-height: 1.4; opacity: 0.9;">
                    Мы уважаем вашу конфиденциальность. Ваши данные используются только для 
                    предоставления услуг и не передаются третьим лицам.
                </p>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h4 style="color: #FFD700; margin-bottom: 10px;">⚠️ Отказ от ответственности</h4>
                <p style="font-size: 14px; line-height: 1.4; opacity: 0.9;">
                    Результаты гаданий не являются профессиональными предсказаниями. 
                    Принимайте решения, основываясь на собственном разуме и интуиции.
                </p>
            </div>
            
            <button onclick="closeModal()" style="
                width: 100%;
                padding: 12px;
                background: #FFD700;
                color: #8B4513;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                cursor: pointer;
                margin-top: 10px;
            ">👌 Понятно</button>
        </div>
    `;
    
    document.body.appendChild(modal);
}

function showDeveloperInfo() {
    // Модальное окно с информацией о разработчике
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;
    
    modal.innerHTML = `
        <div style="
            background: linear-gradient(135deg, #8B4513 0%, #A0522D 100%);
            padding: 20px;
            border-radius: 15px;
            width: 90%;
            max-width: 400px;
            border: 2px solid #FFD700;
            text-align: center;
        ">
            <h3 style="color: #FFD700; margin-bottom: 15px;">👨‍💻 Разработчик</h3>
            
            <div style="margin: 15px 0;">
                <p style="margin: 10px 0; opacity: 0.9;">Аркана - Таро бот</p>
                <p style="margin: 10px 0; opacity: 0.9;">Версия 1.0.0</p>
            </div>
            
            <div style="margin: 20px 0;">
                <p style="margin: 10px 0; opacity: 0.9;">📧 Email для связи:</p>
                <p style="color: #FFD700; font-weight: bold;">your-email@example.com</p>
            </div>
            
            <div style="margin: 15px 0;">
                <p style="font-size: 12px; opacity: 0.7;">
                    С любовью к магии и технологиям 💫
                </p>
            </div>
            
            <button onclick="closeModal()" style="
                width: 100%;
                padding: 12px;
                background: #FFD700;
                color: #8B4513;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                cursor: pointer;
                margin-top: 10px;
            ">✨ Закрыть</button>
        </div>
    `;
    
    document.body.appendChild(modal);
}

// Загрузка баланса пользователя
document.addEventListener('DOMContentLoaded', function() {
    // Загружаем баланс из localStorage (в реальном приложении - из API)
    const balance = localStorage.getItem('userBalance') || 7;
    updateBalanceDisplay(balance);
    
    // Инициализация реферальных данных
    initializeReferralData();
    
    // Проверяем, если баланс низкий - показываем анимацию
    if (balance <= 3) {
        const balanceElement = document.getElementById('balanceAmount');
        balanceElement.classList.add('low-balance', 'pulse');
    }
});

function updateBalanceDisplay(balance) {
    const balanceElement = document.getElementById('balanceAmount');
    if (balanceElement) {
        balanceElement.textContent = balance + ' сообщений';
        
        // Обновляем классы в зависимости от баланса
        balanceElement.classList.remove('low-balance', 'pulse');
        if (balance <= 3) {
            balanceElement.classList.add('low-balance');
            if (balance <= 1) {
                balanceElement.classList.add('pulse');
            }
        }
    }
}

function initializeReferralData() {
    // Инициализация реферальной системы
    if (!localStorage.getItem('referralStats')) {
        const defaultStats = {
            friendsCount: 0,
            bonusCount: 0,
            earnedCount: 0
        };
        localStorage.setItem('referralStats', JSON.stringify(defaultStats));
    }
    
    // Инициализация ID пользователя если нет
    if (!localStorage.getItem('userId')) {
        const userId = Math.random().toString(36).substr(2, 9);
        localStorage.setItem('userId', userId);
    }
}

// Функция для обновления баланса (может вызываться извне)
window.updateBalance = function(newBalance) {
    localStorage.setItem('userBalance', newBalance);
    updateBalanceDisplay(newBalance);
};

// Имитация получения уведомления о пополнении баланса
function simulateBalanceUpdate() {
    const newBalance = Math.floor(Math.random() * 100) + 10;
    updateBalance(newBalance);
    alert(`🎉 Баланс обновлен! Теперь у вас ${newBalance} сообщений`);
}

// Для тестирования - можно вызвать simulateBalanceUpdate() в консоли
window.simulateBalanceUpdate = simulateBalanceUpdate;