let selectedOption = null;

function selectOption(questions, price) {
    selectedOption = { questions, price };
    
    // Убираем выделение у всех
    document.querySelectorAll('.option').forEach(opt => {
        opt.classList.remove('selected');
    });
    
    // Добавляем выделение выбранному
    event.currentTarget.classList.add('selected');
}

async function processPayment(method) {
    if (!selectedOption) {
        alert('Выберите количество вопросов!');
        return;
    }
    
    const userId = localStorage.getItem('userId');
    
    // В реальном проекте здесь будет вызов ЮKassa API
    // Это пример для демонстрации
    const paymentData = {
        userId: userId,
        questions: selectedOption.questions,
        amount: selectedOption.price,
        method: method
    };
    
    try {
        // Отправляем данные на сервер для создания платежа
        const response = await fetch('https://ваш-сервер/api/payment/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(paymentData)
        });
        
        const data = await response.json();
        
        if (data.payment_url) {
            // Перенаправляем на страницу оплаты ЮKassa
            window.open(data.payment_url, '_blank');
        } else {
            // Для теста сразу начисляем
            const currentBalance = parseInt(document.getElementById('balanceCount').textContent);
            const newBalance = currentBalance + selectedOption.questions;
            document.getElementById('balanceCount').textContent = newBalance;
            localStorage.setItem('balance', newBalance);
            
            alert(`✅ Оплата успешна! Получено ${selectedOption.questions} вопросов.`);
            closePayment();
        }
    } catch (error) {
        alert('Ошибка при обработке платежа: ' + error.message);
    }
}