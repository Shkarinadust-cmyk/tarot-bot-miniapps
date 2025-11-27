// Обработка платежей через ЮКассу
async function processPayment(method) {
    const user = Telegram.WebApp.initDataUnsafe?.user;
    if (!user) {
        alert('Ошибка: пользователь не найден');
        return;
    }

    const packages = {
        100: { price: 300, url: 'https://yookassa.ru/my/i/aRWz8G2MdcMQ/l' },
        200: { price: 600, url: 'https://yookassa.ru/my/i/aRW0Hp0pnJY4/l' },
        300: { price: 900, url: 'https://yookassa.ru/my/i/aRW0ONaTgvr4/l' },
        500: { price: 1500, url: 'https://yookassa.ru/my/i/aRW0UpykQRFm/l' },
        1000: { price: 3000, url: 'https://yookassa.ru/my/i/aRW0auBkhbht/l' }
    };

    const selected = packages[selectedPackage];
    if (!selected) {
        alert('Выберите пакет сообщений');
        return;
    }

    try {
        // Перенаправляем на страницу оплаты ЮКассы
        const paymentUrl = `${selected.url}?user_id=${user.id}&amount=${selectedPackage}`;
        Telegram.WebApp.openInvoice(paymentUrl, function(status) {
            if (status === 'paid') {
                alert(`✅ Оплата прошла успешно! Вам начислено ${selectedPackage} вопросов.`);
                closeModal();
            } else {
                alert('❌ Оплата не прошла. Попробуйте еще раз.');
            }
        });
        
    } catch (error) {
        console.error('Payment error:', error);
        alert('Ошибка при обработке платежа');
    }
}