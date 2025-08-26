from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
import os
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///field_supervision.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Simple User model for demo
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_authenticated(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        flash('Demo: Login functionality would work here', 'info')
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        flash('Demo: Registration functionality would work here', 'info')
    return render_template('auth/register.html')

@app.route('/dashboard')
def dashboard():
    # Demo dashboard
    stats = {
        'total_applications': 5,
        'pending_applications': 2,
        'approved_applications': 2,
        'in_progress_applications': 1,
        'total_reports': 8
    }
    
    # Create a demo user for display
    demo_user = type('DemoUser', (), {
        'first_name': 'John',
        'last_name': 'Doe',
        'course': 'B.Sc. Computer Science',
        'university': 'University of Ghana',
        'role': 'student'
    })()
    
    return render_template('student/dashboard.html', 
                         current_user=demo_user,
                         stats=stats,
                         applications=[],
                         recent_reports=[],
                         notifications=[])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("🎓 Field Supervision Management System")
    print("🌍 Designed for African Universities and Colleges")
    print("📧 Visit: http://localhost:5000")
    print("-" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)