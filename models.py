from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from teacher_form2 import db

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    teaching_years = db.Column(db.String(100))
    subjects = db.Column(db.String(200))
    join_date = db.Column(db.DateTime, default=datetime.now)
    
    # العلاقات
    form_requests = db.relationship('FormRequest', backref='teacher', lazy=True)
    messages = db.relationship('Message', backref='teacher', lazy=True)
    
    def __repr__(self):
        return f"Teacher('{self.username}', '{self.name}')"

class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(200))
    
    # العلاقات
    requests = db.relationship('FormRequest', backref='form', lazy=True)
    
    def __repr__(self):
        return f"Form('{self.name}')"

class FormRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    form_id = db.Column(db.Integer, db.ForeignKey('form.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    request_date = db.Column(db.DateTime, default=datetime.now)
    needed_by_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    response_message = db.Column(db.Text)
    response_date = db.Column(db.DateTime)
    pickup_location = db.Column(db.String(200))
    
    def __repr__(self):
        return f"FormRequest('{self.teacher.name}', '{self.form.name}', '{self.status}')"

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    read = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"Message('{self.subject}', '{self.date}')"