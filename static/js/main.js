// إعداد وظائف عامة
document.addEventListener('DOMContentLoaded', function() {
    // تنفيذ التاريخ الحالي في التذييل
    const currentYear = new Date().getFullYear();
    const footerYear = document.querySelector('footer p');
    if (footerYear) {
        footerYear.innerHTML = footerYear.innerHTML.replace('{{ current_year }}', currentYear);
    }
    
    // إخفاء تنبيهات الرسائل بعد 5 ثوانٍ
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 500);
        }, 5000);
    });
});