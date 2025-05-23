from flask import render_template, request, redirect, url_for, flash, session
from datetime import datetime
from models import Teacher, Form, FormRequest, Message
from teacher_form2 import app, db
from werkzeug.security import check_password_hash

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        teacher = Teacher.query.filter_by(username=username).first()
        
        if teacher and check_password_hash(teacher.password, password):
            session['user_id'] = teacher.id
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('تم تسجيل الخروج بنجاح!', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    teacher = Teacher.query.get(session['user_id'])
    pending_requests = FormRequest.query.filter_by(teacher_id=teacher.id, status='pending').count()
    approved_requests = FormRequest.query.filter_by(teacher_id=teacher.id, status='approved').count()
    rejected_requests = FormRequest.query.filter_by(teacher_id=teacher.id, status='rejected').count()
    unread_messages = Message.query.filter_by(teacher_id=teacher.id, read=False).count()
    
    return render_template('dashboard.html', teacher=teacher, 
                           pending_requests=pending_requests, 
                           approved_requests=approved_requests, 
                           rejected_requests=rejected_requests,
                           unread_messages=unread_messages)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    teacher = Teacher.query.get(session['user_id'])
    
    if request.method == 'POST':
        teacher.name = request.form.get('name')
        teacher.email = request.form.get('email')
        teacher.phone = request.form.get('phone')
        teacher.teaching_years = request.form.get('teaching_years')
        teacher.subjects = request.form.get('subjects')
        
        db.session.commit()
        flash('تم تحديث الملف الشخصي بنجاح!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', teacher=teacher)

@app.route('/forms')
def forms():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    available_forms = Form.query.all()
    teacher_id = session['user_id']
    form_requests = FormRequest.query.filter_by(teacher_id=teacher_id).all()
    
    return render_template('forms.html', forms=available_forms, form_requests=form_requests)

@app.route('/request_form', methods=['POST'])
def request_form():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    form_id = request.form.get('form_id')
    reason = request.form.get('reason')
    needed_by_date = request.form.get('needed_by_date')
    
    new_request = FormRequest(
        teacher_id=session['user_id'],
        form_id=form_id,
        reason=reason,
        needed_by_date=datetime.strptime(needed_by_date, '%Y-%m-%d'),
        request_date=datetime.now(),
        status='pending'
    )
    
    db.session.add(new_request)
    db.session.commit()
    
    flash('تم إرسال طلب الاستمارة بنجاح!', 'success')
    return redirect(url_for('forms'))

@app.route('/mail')
def mail():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    teacher_id = session['user_id']
    messages = Message.query.filter_by(teacher_id=teacher_id).order_by(Message.date.desc()).all()
    
    # تحديث حالة القراءة للرسائل
    for message in messages:
        message.read = True
    
    db.session.commit()
    
    return render_template('mail.html', messages=messages)