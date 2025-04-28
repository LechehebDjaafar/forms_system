project/
├── app.py                     # ملف Python الرئيسي للتطبيق 
├── static/                    # المحتويات الثابتة
│   ├── css/
│   │   ├── main.css           # تنسيقات CSS الرئيسية
│   │   └── login.css          # تنسيقات صفحة تسجيل الدخول
│   ├── js/
│   │   ├── main.js            # وظائف JavaScript الرئيسية
│   │   └── forms.js           # وظائف خاصة بالاستمارات
│   └── images/                # صور الموقع
├── templates/                 # قوالب HTML
│   ├── base.html              # القالب الأساسي
│   ├── login.html             # صفحة تسجيل الدخول
│   ├── dashboard.html         # لوحة التحكم الرئيسية للأستاذ
│   ├── profile.html           # الملف الشخصي للأستاذ
│   ├── forms.html             # صفحة طلب الاستمارات
│   └── mail.html              # صفحة البريد والإشعارات
├── instance/
│   └── teachers.db            # قاعدة بيانات SQLite
├── models.py                  # نماذج قاعدة البيانات
├── routes.py                  # مسارات التطبيق
└── requirements.txt           # متطلبات التثبيت