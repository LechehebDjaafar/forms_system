// وظائف خاصة بصفحة الاستمارات
document.addEventListener('DOMContentLoaded', function() {
    // فتح علامة التبويب المحددة
    window.openTab = function(evt, tabName) {
        const tabContents = document.getElementsByClassName("tab-content");
        for (let i = 0; i < tabContents.length; i++) {
            tabContents[i].classList.remove("active");
        }
        
        const tabButtons = document.getElementsByClassName("tab-btn");
        for (let i = 0; i < tabButtons.length; i++) {
            tabButtons[i].classList.remove("active");
        }
        
        document.getElementById(tabName).classList.add("active");
        evt.currentTarget.classList.add("active");
    };
    
    // فتح النافذة المنبثقة لطلب استمارة
    const requestButtons = document.querySelectorAll('.request-form');
    const requestModal = document.getElementById('request-form-modal');
    const closeBtn = requestModal?.querySelector('.close');
    
    requestButtons.forEach(button => {
        button.addEventListener('click', function() {
            const formId = this.getAttribute('data-form-id');
            const formName = this.getAttribute('data-form-name');
            
            document.getElementById('form_id').value = formId;
            document.getElementById('form-name').textContent = formName;
            
            requestModal.style.display = 'block';
        });
    });
    
    // إغلاق النافذة المنبثقة
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            requestModal.style.display = 'none';
        });
    }
    
    // إغلاق النافذة عند النقر خارجها
    window.addEventListener('click', function(event) {
        if (event.target == requestModal) {
            requestModal.style.display = 'none';
        }
    });
    
    // فتح النافذة المنبثقة لتفاصيل الطلب
    const viewDetailsButtons = document.querySelectorAll('.view-details');
    const detailsModal = document.getElementById('request-details-modal');
    const detailsCloseBtn = detailsModal?.querySelector('.close');
    
    viewDetailsButtons.forEach(button => {
        button.addEventListener('click', function() {
            const requestId = this.getAttribute('data-request-id');
            
            // يمكن هنا إرسال طلب AJAX للحصول على تفاصيل الطلب
            // ولكن للتبسيط سنستخدم بيانات وهمية
            document.getElementById('request-details').innerHTML = `
                <div class="details-item">
                    <strong>رقم الطلب:</strong> ${requestId}
                </div>
                <div class="details-item">
                    <strong>سبب الطلب:</strong> طلب الاستمارة لأغراض إدارية
                </div>
                <div class="details-item">
                    <strong>تاريخ الطلب:</strong> 2023-10-10
                </div>
                <div class="details-item">
                    <strong>التاريخ المطلوب:</strong> 2023-10-15
                </div>
                <div class="details-item">
                    <strong>تعليق الإدارة:</strong> 
                    <p>سيتم معالجة طلبك في أقرب وقت ممكن.</p>
                </div>
            `;
            
            detailsModal.style.display = 'block';
        });
    });
    
    // إغلاق نافذة التفاصيل
    if (detailsCloseBtn) {
        detailsCloseBtn.addEventListener('click', function() {
            detailsModal.style.display = 'none';
        });
    }
    
    // إغلاق نافذة التفاصيل عند النقر خارجها
    window.addEventListener('click', function(event) {
        if (event.target == detailsModal) {
            detailsModal.style.display = 'none';
        }
    });
});