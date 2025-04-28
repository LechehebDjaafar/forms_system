from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
import os
from datetime import datetime
import io
from werkzeug.security import generate_password_hash, check_password_hash
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key'  # يجب تغييره في الإنتاج

# إنشاء المجلدات المطلوبة إذا لم تكن موجودة
if not os.path.exists('static'):
    os.makedirs('static')
if not os.path.exists('static/images'):
    os.makedirs('static/images')
if not os.path.exists('static/forms'):
    os.makedirs('static/forms')

# إنشاء قاعدة بيانات SQLite
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # جدول المعلمين
    c.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            name TEXT,
            years_taught TEXT,
            email TEXT,
            phone TEXT,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    
    # جدول طلبات الاستمارات
    c.execute('''
        CREATE TABLE IF NOT EXISTS form_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            form_type TEXT,
            reason TEXT,
            date TEXT,
            status TEXT DEFAULT 'pending',
            approval_date TEXT,
            form_path TEXT,
            admin_notes TEXT,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id)
        )
    ''')
    
    # إدخال مستخدم تجريبي
    try:
        c.execute("INSERT INTO teachers (username, password, name, years_taught, is_admin) VALUES (?, ?, ?, ?, ?)", 
                 ('teacher1', generate_password_hash('password123'), 'أحمد محمد', 'السنة الأولى, السنة الثانية', 0))
    except sqlite3.IntegrityError:
        pass  # المستخدم موجود بالفعل
    
    # إدخال مستخدم مدير تجريبي
    try:
        c.execute("INSERT INTO teachers (username, password, name, years_taught, is_admin) VALUES (?, ?, ?, ?, ?)", 
                 ('admin', generate_password_hash('admin123'), 'مدير النظام', 'جميع السنوات', 1))
    except sqlite3.IntegrityError:
        pass  # المستخدم موجود بالفعل
    
    conn.commit()
    conn.close()

init_db()

# دالة مساعدة للتحقق من تسجيل الدخول
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يرجى تسجيل الدخول أولاً', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# دالة مساعدة للتحقق من صلاحيات المدير
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يرجى تسجيل الدخول أولاً', 'error')
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def home():
    if 'user_id' in session:
        if session.get('is_admin'):
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('teacher_home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM teachers WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['name'] = user['name']
            session['is_admin'] = user['is_admin']
            flash('تم تسجيل الدخول بنجاح', 'success')
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('teacher_home'))
        else:
            flash('خطأ في اسم المستخدم أو كلمة المرور', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        name = request.form['name']
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        years_taught = ', '.join(request.form.getlist('years_taught'))
        
        if password != confirm_password:
            flash('كلمات المرور غير متطابقة', 'error')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("""
                INSERT INTO teachers (username, password, name, years_taught, email, phone) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, hashed_password, name, years_taught, email, phone))
            conn.commit()
            conn.close()
            
            flash('تم إنشاء الحساب بنجاح، يمكنك الآن تسجيل الدخول', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('اسم المستخدم موجود بالفعل', 'error')
            
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return redirect(url_for('teacher_home'))

@app.route('/teacher/home')
@login_required
def teacher_home():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # جلب معلومات المعلم
    c.execute("SELECT * FROM teachers WHERE id=?", (session['user_id'],))
    teacher = c.fetchone()
    
    # إحصائيات الاستمارات
    c.execute("""
        SELECT 
            COUNT(*) as total_forms,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_forms,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_forms,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_forms
        FROM form_requests 
        WHERE teacher_id=?
    """, (session['user_id'],))
    stats = c.fetchone()
    
    # آخر الاستمارات المعتمدة
    c.execute("""
        SELECT id, form_type, date, status, approval_date 
        FROM form_requests 
        WHERE teacher_id=? AND status='approved'
        ORDER BY approval_date DESC LIMIT 3
    """, (session['user_id'],))
    recent_approved = c.fetchall()
    
    # آخر طلبات الاستمارات
    c.execute("""
        SELECT id, form_type, date, status
        FROM form_requests 
        WHERE teacher_id=?
        ORDER BY id DESC LIMIT 5
    """, (session['user_id'],))
    recent_requests = c.fetchall()
    
    conn.close()
    
    return render_template('teacher_home.html', 
                           teacher=teacher,
                           stats=stats,
                           recent_approved=recent_approved,
                           recent_requests=recent_requests)

@app.route('/teacher/profile')
@login_required
def teacher_profile():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM teachers WHERE id=?", (session['user_id'],))
    teacher = c.fetchone()
    
    conn.close()
    
    return render_template('teacher_profile.html', teacher=teacher)

@app.route('/teacher/profile/update', methods=['POST'])
@login_required
def update_profile():
    name = request.form['name']
    email = request.form.get('email', '')
    phone = request.form.get('phone', '')
    years_taught = ', '.join(request.form.getlist('years_taught'))
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # تحديث المعلومات الأساسية
    c.execute("""
        UPDATE teachers 
        SET name=?, email=?, phone=?, years_taught=?
        WHERE id=?
    """, (name, email, phone, years_taught, session['user_id']))
    
    # تحديث كلمة المرور إذا طلب ذلك
    if new_password:
        c.execute("SELECT password FROM teachers WHERE id=?", (session['user_id'],))
        user = c.fetchone()
        
        if not check_password_hash(user['password'], current_password):
            conn.close()
            flash('كلمة المرور الحالية غير صحيحة', 'error')
            return redirect(url_for('teacher_profile'))
        
        if new_password != confirm_password:
            conn.close()
            flash('كلمات المرور الجديدة غير متطابقة', 'error')
            return redirect(url_for('teacher_profile'))
        
        hashed_password = generate_password_hash(new_password)
        c.execute("UPDATE teachers SET password=? WHERE id=?", (hashed_password, session['user_id']))
    
    conn.commit()
    conn.close()
    
    # تحديث اسم المستخدم في الجلسة
    session['name'] = name
    
    flash('تم تحديث المعلومات الشخصية بنجاح', 'success')
    return redirect(url_for('teacher_profile'))

@app.route('/teacher/request_form', methods=['GET', 'POST'])
@login_required
def request_form():
    if request.method == 'POST':
        form_type = request.form['form_type']
        reason = request.form['reason']
        date = request.form['date']
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO form_requests (teacher_id, form_type, reason, date) 
            VALUES (?, ?, ?, ?)
        """, (session['user_id'], form_type, reason, date))
        conn.commit()
        conn.close()
        
        flash('تم إرسال طلب الاستمارة بنجاح، سيتم مراجعته من قبل الإدارة', 'success')
        return redirect(url_for('teacher_forms'))
    
    return render_template('request_form.html')

@app.route('/teacher/forms')
@login_required
def teacher_forms():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # جلب جميع طلبات الاستمارات للمعلم
    c.execute("""
        SELECT id, form_type, reason, date, status, approval_date, admin_notes 
        FROM form_requests 
        WHERE teacher_id=? 
        ORDER BY id DESC
    """, (session['user_id'],))
    
    form_requests = []
    for row in c.fetchall():
        status_text = "قيد المراجعة"
        if row['status'] == 'approved':
            status_text = "تمت الموافقة"
        elif row['status'] == 'rejected':
            status_text = "تم الرفض"
        
        form_requests.append({
            'id': row['id'],
            'form_type': row['form_type'],
            'reason': row['reason'],
            'date': row['date'],
            'status': row['status'],
            'status_text': status_text,
            'approval_date': row['approval_date'] if row['approval_date'] else '',
            'admin_notes': row['admin_notes'] if row['admin_notes'] else ''
        })
    
    conn.close()
    
    return render_template('teacher_forms.html', form_requests=form_requests)

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # إحصائيات عامة
    c.execute("SELECT COUNT(*) as teacher_count FROM teachers WHERE is_admin = 0")
    teacher_count = c.fetchone()['teacher_count']
    
    c.execute("""
        SELECT 
            COUNT(*) as total_forms,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_forms,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_forms,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_forms
        FROM form_requests
    """)
    stats = c.fetchone()
    
    # طلبات الاستمارات المعلقة
    c.execute("""
        SELECT fr.id, fr.form_type, fr.date, fr.status, t.name as teacher_name
        FROM form_requests fr
        JOIN teachers t ON fr.teacher_id = t.id
        WHERE fr.status = 'pending'
        ORDER BY fr.id DESC LIMIT 10
    """)
    pending_requests = c.fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                           teacher_count=teacher_count,
                           stats=stats,
                           pending_requests=pending_requests)

@app.route('/admin/teachers')
@admin_required
def admin_teachers():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("""
        SELECT t.*, 
            (SELECT COUNT(*) FROM form_requests WHERE teacher_id = t.id) as form_count
        FROM teachers t
        WHERE t.is_admin = 0
        ORDER BY t.id DESC
    """)
    teachers = c.fetchall()
    
    conn.close()
    
    return render_template('admin_teachers.html', teachers=teachers)

@app.route('/admin/create_teacher', methods=['GET', 'POST'])
@admin_required
def admin_create_teacher():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        years_taught = ', '.join(request.form.getlist('years_taught'))
        
        hashed_password = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("""
                INSERT INTO teachers (username, password, name, years_taught, email, phone) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, hashed_password, name, years_taught, email, phone))
            conn.commit()
            conn.close()
            
            flash('تم إنشاء حساب المعلم بنجاح', 'success')
            return redirect(url_for('admin_teachers'))
        except sqlite3.IntegrityError:
            flash('اسم المستخدم موجود بالفعل', 'error')
    
    return render_template('admin_create_teacher.html')

@app.route('/admin/edit_teacher/<int:teacher_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_teacher(teacher_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        years_taught = ', '.join(request.form.getlist('years_taught'))
        new_password = request.form.get('new_password', '')
        
        # تحديث المعلومات الأساسية
        c.execute("""
            UPDATE teachers 
            SET username=?, name=?, email=?, phone=?, years_taught=?
            WHERE id=?
        """, (username, name, email, phone, years_taught, teacher_id))
        
        # تحديث كلمة المرور إذا تم توفيرها
        if new_password:
            hashed_password = generate_password_hash(new_password)
            c.execute("UPDATE teachers SET password=? WHERE id=?", (hashed_password, teacher_id))
        
        conn.commit()
        flash('تم تحديث معلومات المعلم بنجاح', 'success')
        return redirect(url_for('admin_teachers'))
    
    # جلب معلومات المعلم للعرض في النموذج
    c.execute("SELECT * FROM teachers WHERE id=?", (teacher_id,))
    teacher = c.fetchone()
    
    conn.close()
    
    if not teacher:
        flash('المعلم غير موجود', 'error')
        return redirect(url_for('admin_teachers'))
    
    return render_template('admin_edit_teacher.html', teacher=teacher)

@app.route('/admin/delete_teacher/<int:teacher_id>', methods=['POST'])
@admin_required
def admin_delete_teacher(teacher_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # حذف طلبات الاستمارات المرتبطة بهذا المعلم أولاً
    c.execute("DELETE FROM form_requests WHERE teacher_id=?", (teacher_id,))
    
    # ثم حذف المعلم
    c.execute("DELETE FROM teachers WHERE id=?", (teacher_id,))
    
    conn.commit()
    conn.close()
    
    flash('تم حذف المعلم وجميع طلباته بنجاح', 'success')
    return redirect(url_for('admin_teachers'))

@app.route('/admin/forms')
@admin_required
def admin_forms():
    status_filter = request.args.get('status', 'all')
    
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # بناء استعلام SQL بناءً على المرشح
    query = """
        SELECT fr.id, fr.form_type, fr.reason, fr.date, fr.status, t.name as teacher_name
        FROM form_requests fr
        JOIN teachers t ON fr.teacher_id = t.id
    """
    
    params = []
    if status_filter != 'all':
        query += " WHERE fr.status = ?"
        params.append(status_filter)
    
    query += " ORDER BY fr.id DESC"
    
    c.execute(query, params)
    form_requests = c.fetchall()
    
    conn.close()
    
    return render_template('admin_forms.html', form_requests=form_requests, status_filter=status_filter)

@app.route('/admin/form_details/<int:form_id>', methods=['GET', 'POST'])
@admin_required
def admin_form_details(form_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if request.method == 'POST':
        status = request.form['status']
        admin_notes = request.form.get('admin_notes', '')
        
        approval_date = datetime.now().strftime('%Y-%m-%d') if status == 'approved' else None
        
        c.execute("""
            UPDATE form_requests 
            SET status=?, approval_date=?, admin_notes=?
            WHERE id=?
        """, (status, approval_date, admin_notes, form_id))
        
        conn.commit()
        flash('تم تحديث حالة الطلب بنجاح', 'success')
        return redirect(url_for('admin_forms'))
    
    # جلب تفاصيل الطلب
    c.execute("""
        SELECT fr.*, t.name as teacher_name, t.years_taught
        FROM form_requests fr
        JOIN teachers t ON fr.teacher_id = t.id
        WHERE fr.id = ?
    """, (form_id,))
    form_request = c.fetchone()
    
    conn.close()
    
    if not form_request:
        flash('الطلب غير موجود', 'error')
        return redirect(url_for('admin_forms'))
    
    return render_template('admin_form_details.html', form=form_request)

@app.route('/download_form/<int:form_id>')
@login_required
def download_form(form_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # التحقق من صلاحية الوصول إلى الاستمارة
    if session.get('is_admin'):
        c.execute("""
            SELECT fr.*, t.name as teacher_name
            FROM form_requests fr
            JOIN teachers t ON fr.teacher_id = t.id
            WHERE fr.id=? AND fr.status='approved'
        """, (form_id,))
    else:
        c.execute("""
            SELECT fr.*, t.name as teacher_name
            FROM form_requests fr
            JOIN teachers t ON fr.teacher_id = t.id
            WHERE fr.id=? AND fr.teacher_id=? AND fr.status='approved'
        """, (form_id, session['user_id']))
    
    form = c.fetchone()
    conn.close()
    
    if not form:
        flash('لا يمكن تنزيل هذه الاستمارة', 'error')
        return redirect(url_for('dashboard'))
    
    # إنشاء ملف PDF
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(width / 2, height - 50, form['form_type'])
    
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 100, f"اسم المعلم: {form['teacher_name']}")
    pdf.drawString(50, height - 120, f"رقم الطلب: {form_id}")
    pdf.drawString(50, height - 140, f"تاريخ الطلب: {form['date']}")
    pdf.drawString(50, height - 160, f"تاريخ الاعتماد: {form['approval_date']}")
    
    pdf.drawString(50, height - 200, f"نوع الاستمارة: {form['form_type']}")
    pdf.drawString(50, height - 220, f"سبب الطلب: {form['reason']}")
    
    pdf.drawString(50, height - 300, "توقيع المعلم: ______________")
    pdf.drawString(300, height - 300, "توقيع الإدارة: ______________")
    
    pdf.showPage()
    pdf.save()
    
    buffer.seek(0)
    
    form_name = f"{form['form_type'].replace(' ', '_')}_{form_id}.pdf"
    return send_file(buffer, as_attachment=True, download_name=form_name, mimetype='application/pdf')

@app.route('/api/stats')
@login_required
def api_stats():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # إحصائيات للمعلم
    c.execute("""
        SELECT
            form_type,
            COUNT(*) as count,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
        FROM form_requests
        WHERE teacher_id = ?
        GROUP BY form_type
    """, (session['user_id'],))
    
    form_stats = []
    for row in c.fetchall():
        form_stats.append({
            'form_type': row['form_type'],
            'count': row['count'],
            'approved': row['approved'],
            'rejected': row['rejected'],
            'pending': row['pending']
        })
    
    conn.close()
    
    return json.dumps(form_stats)

@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)