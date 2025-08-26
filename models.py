from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# This will be initialized in app.py
db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False)  # student, supervisor, admin, organization
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Student-specific fields
    student_id = db.Column(db.String(20), unique=True)
    course = db.Column(db.String(100))
    year_of_study = db.Column(db.Integer)
    university = db.Column(db.String(100))
    department = db.Column(db.String(100))
    
    # Organization-specific fields
    organization_name = db.Column(db.String(100))
    organization_type = db.Column(db.String(50))
    registration_number = db.Column(db.String(50))
    
    # Relationships
    applications = db.relationship('Application', backref='student', lazy=True, foreign_keys='Application.student_id')
    supervised_applications = db.relationship('Application', backref='supervisor', lazy=True, foreign_keys='Application.supervisor_id')
    reports = db.relationship('Report', backref='student', lazy=True)
    sent_notifications = db.relationship('Notification', backref='sender', lazy=True, foreign_keys='Notification.sender_id')
    received_notifications = db.relationship('Notification', backref='recipient', lazy=True, foreign_keys='Notification.recipient_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # government, private, ngo, etc.
    location = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    placements = db.relationship('Placement', backref='organization', lazy=True)

class Placement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    requirements = db.Column(db.Text)
    available_slots = db.Column(db.Integer, default=1)
    filled_slots = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application', backref='placement', lazy=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    placement_id = db.Column(db.Integer, db.ForeignKey('placement.id'))
    supervisor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Application details
    application_type = db.Column(db.String(50), nullable=False)  # teaching_practice, internship, industrial_attachment
    preferred_location = db.Column(db.String(100))
    cv_filename = db.Column(db.String(255))
    cover_letter = db.Column(db.Text)
    additional_documents = db.Column(db.Text)  # JSON string of filenames
    
    # Status and dates
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, in_progress, completed
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    
    # Admin comments
    admin_comments = db.Column(db.Text)
    supervisor_comments = db.Column(db.Text)
    
    # Relationships
    reports = db.relationship('Report', backref='application', lazy=True)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Report details
    report_type = db.Column(db.String(20), nullable=False)  # weekly, monthly, final
    week_number = db.Column(db.Integer)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    activities = db.Column(db.Text)
    challenges = db.Column(db.Text)
    learning_outcomes = db.Column(db.Text)
    
    # File attachments
    attachments = db.Column(db.Text)  # JSON string of filenames
    
    # Status and feedback
    status = db.Column(db.String(20), default='submitted')  # submitted, approved, revision_required
    supervisor_feedback = db.Column(db.Text)
    supervisor_rating = db.Column(db.Integer)  # 1-5 scale
    feedback_date = db.Column(db.DateTime)
    
    # Timestamps
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # present, absent, late, excused
    check_in_time = db.Column(db.Time)
    check_out_time = db.Column(db.Time)
    notes = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Evaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    evaluator_type = db.Column(db.String(20), nullable=False)  # supervisor, organization
    
    # Evaluation criteria (1-5 scale)
    punctuality = db.Column(db.Integer)
    professionalism = db.Column(db.Integer)
    communication = db.Column(db.Integer)
    technical_skills = db.Column(db.Integer)
    teamwork = db.Column(db.Integer)
    initiative = db.Column(db.Integer)
    overall_performance = db.Column(db.Integer)
    
    # Feedback
    strengths = db.Column(db.Text)
    areas_for_improvement = db.Column(db.Text)
    additional_comments = db.Column(db.Text)
    recommendation = db.Column(db.String(20))  # excellent, good, satisfactory, needs_improvement, unsatisfactory
    
    # Timestamps
    evaluation_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # info, warning, success, error
    is_read = db.Column(db.Boolean, default=False)
    email_sent = db.Column(db.Boolean, default=False)
    sms_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)