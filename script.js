// Этот файл будет обновлен после настройки бота и базы данных
// Пока что это просто заглушки для демонстрации

function copyLink() {
    const linkText = document.getElementById('userLink').innerText;
    navigator.clipboard.writeText(linkText).then(() => {
        alert('Ссылка скопирована!');
    });
}

function shareLink() {
    const linkText = document.getElementById('userLink').innerText;
    const shareText = `Привет! Попробуй этого классного бота-таро: ${linkText}`;
    
    if (navigator.share) {
        navigator.share({
            title: 'Аркана - Таро бот',
            text: shareText,
            url: linkText
        });
    } else {
        navigator.clipboard.writeText(shareText).then(() => {
            alert('Сообщение скопировано! Теперь вы можете отправить его друзьям.');
        });
    }
}

function saveSettings() {
    const isEnabled = document.getElementById('adviceToggle').checked;
    const time = document.getElementById('timeSelect').value;
    
    alert(`Настройки сохранены! Совет дня ${isEnabled ? 'включен' : 'выключен'} на время ${time}`);
    // Здесь будет код для сохранения настроек на сервере
}